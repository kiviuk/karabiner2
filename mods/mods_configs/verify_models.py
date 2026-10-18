#!/usr/bin/env python3
"""
verify_models.py — Verify models in a mods.yml backup against live provider APIs.

Reads a mods.yml backup file, queries **public** provider APIs to obtain the
current set of available models, and produces a structured report showing
whether each configured model is:

    current  — model still exists under the same name
    renamed  — model exists under a different name (old → new)
    deleted  — model no longer exists on the provider

The report is a generic, machine-readable format (JSON by default; optional
YAML or Markdown) that a *second* script can consume to update the original
mods.yml in one pass:

    current  → keep the entry as-is
    renamed  → replace old_model with new_model (carry over aliases)
    deleted  → remove or comment out the entry

No API tokens / keys are required.  Every data source is public:

    openrouter  → https://openrouter.ai/api/v1/models  (public JSON API)
    nvidia      → https://integrate.api.nvidia.com/v1/models  (unauthenticated)
    deepseek    → cross-referenced via OpenRouter (deepseek/ author prefix)
                  plus dynamic rename discovery from DeepSeek change-log
    alibaba     → cross-referenced via OpenRouter (qwen/ author prefix)
                  plus model IDs extracted from Alibaba Model Studio docs
    alibaba_eu  → same as alibaba (different region endpoint)

All progress / diagnostic output goes to **stderr** so that stdout (or shell
redirection) contains *only* the report:

    python3 verify_models.py --md > report.md        # stdout = report only
    python3 verify_models.py --out report.md         # file = report only

Usage:
    python3 verify_models.py [backup.yml] [--out report.json] [--yaml|--md] [--verbose]
"""

import argparse
import glob
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from difflib import get_close_matches, SequenceMatcher
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────

# Where to look for the backup file if the user doesn't pass one explicitly.
# Supports glob patterns (e.g. "mods.yml.bak*") — resolved by resolve_backup(),
# which picks the most recently modified match (CR #1).
CANDIDATE_BACKUPS = [
    "mods.yml.bak*",        # glob: newest mods.yml.bak.* (e.g. mods.yml.bak.20261017-120406)
    "mods.yml.bak",
    "/Users/mobe/.config/mods/mods_configs/mods.yml.bak*",
    "/Users/mobe/.config/mods/mods.yml.bak*",
]

# Public model-directory endpoints (no auth required).
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
NVIDIA_MODELS_URL = "https://integrate.api.nvidia.com/v1/models"

HTTP_TIMEOUT = 30       # seconds for full API calls
FAST_TIMEOUT = 8        # seconds for quick probes / fallbacks
FUZZY_CUTOFF = 0.70    # similarity threshold for rename suggestions
MAX_RETRIES = 2        # network retry attempts
RETRY_DELAY = 2        # seconds between retries

# For providers whose own API requires authentication, cross-reference
# OpenRouter's public model directory.  A backup model ID like
# "deepseek-v4-pro" is looked up as "deepseek/deepseek-v4-pro" on OpenRouter,
# then the author prefix is stripped to get back the bare ID.
CROSSREF_PREFIX = {
    "deepseek":   "deepseek/",
    "alibaba":    "qwen/",
    "alibaba_eu": "qwen/",
}

# Provider documentation / change-log URLs — used to auto-discover renames
# when the provider's own API requires authentication (CR #2).
RENAME_DOC_URLS = {
    "deepseek":   "https://api-docs.deepseek.com/updates/",
    "alibaba":    "https://help.aliyun.com/en/model-studio/list-models",
    "alibaba_eu": "https://help.aliyun.com/en/model-studio/list-models",
}

# Base-known renames (fallback).  These are merged with dynamically discovered
# renames from provider docs/changelogs (see discover_renames()).
#
# Sources:
#   DeepSeek changelog (api-docs.deepseek.com/updates):
#     "the legacy names deepseek-v4-flash and deepseek-v4-flash-vision-exp
#      are still accepted, but the corresponding models have been retired;
#      their requests are served by DeepSeek-V4.1-Flash-1017"
#   Alibaba Model Studio docs (help.aliyun.com/.../list-models):
#     example model ID: "qwen3.8-max"  (exact)
KNOWN_RENAMES = {
    "deepseek": {
        "deepseek-v4-flash": "deepseek-v4.1-flash-1017",
    },
    "alibaba": {
        "qwen3.8-plus": "qwen3.8-max",
    },
    "alibaba_eu": {
        "qwen3.8-plus": "qwen3.8-max",
    },
}


# ──────────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────────

def say(msg=""):
    """Print a progress / diagnostic message to **stderr**.

    All progress, phase markers, and per-model diagnostics use this so that
    stdout remains clean for the report output.
    """
    print(msg, file=sys.stderr)


def resolve_backup(pattern):
    """Resolve a backup file path, expanding glob patterns (CR #1).

    If *pattern* is an exact file path it is returned as-is.  If it contains
    glob wildcards (``*``, ``?``) or matches no exact file, ``glob.glob``
    is used to find candidates and the most recently modified one is chosen.

    Returns the resolved path string, or ``None`` if nothing matches.
    """
    p = Path(pattern)
    if p.is_file():
        return str(p)
    matches = sorted(glob.glob(pattern), key=lambda f: Path(f).stat().st_mtime, reverse=True)
    return matches[0] if matches else None


# ──────────────────────────────────────────────────────────────────────────
# Minimal mods.yml parser (no PyYAML / external deps)
# ──────────────────────────────────────────────────────────────────────────

def parse_mods_yml(path):
    """Parse a mods.yml file and return a dict:

        {provider: {"base-url": str, "api-key-cmd": str,
                     "models": {model_id: {"aliases": [str]}}}}

    Only the ``apis:`` section is parsed.  Handles model IDs containing
    colons (e.g. ``qwen3.8-27b:free``) by detecting the trailing ``:``
    that YAML uses as a key separator.
    """
    providers = {}
    # Parsing context tracked across lines
    sect = None          # top-level section name (e.g. "apis")
    prov = None          # current provider name
    model = None         # current model ID
    in_models = False    # are we inside a provider's `models:` block?

    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            text = line.strip()

            # ── Top-level key (indent 0) ──────────────────────────────
            if indent == 0:
                sect = text.rstrip(":").strip()
                prov = None
                model = None
                in_models = False
                continue

            if sect != "apis":
                continue

            # ── Provider block (indent 2) ─────────────────────────────
            if indent == 2 and text.endswith(":"):
                prov = text[:-1].strip()
                providers[prov] = {"base-url": "", "api-key-cmd": "", "models": {}}
                in_models = False
                continue

            # ── Provider properties (indent 4) ────────────────────────
            if prov and indent == 4:
                if text == "models:":
                    in_models = True
                    model = None
                elif ":" in text:
                    key, val = text.split(":", 1)
                    val = val.strip().strip('"').strip("'")
                    key = key.strip()
                    if key in ("base-url", "api-key-cmd"):
                        providers[prov][key] = val
                continue

            # ── Model ID (indent 6, under models:) ────────────────────
            if in_models and indent == 6 and text.endswith(":"):
                model = text[:-1].strip()
                providers[prov]["models"][model] = {"aliases": []}
                continue

            # ── Model properties (indent 8) ───────────────────────────
            if model and indent == 8:
                if text.startswith("aliases:"):
                    m = re.search(r"\[(.*)\]", text)
                    if m:
                        providers[prov]["models"][model]["aliases"] = \
                            re.findall(r'"([^"]*)"', m.group(1))
                # max-input-chars, etc. — not needed for verification
                continue

    return providers


# ──────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────────────────────────────────

def _http_get_json(url, timeout=HTTP_TIMEOUT, retries=MAX_RETRIES):
    """GET a JSON endpoint with simple retry logic.  Returns parsed JSON or None."""
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "mods-verify/1.0", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            # 401/403 = auth required → silent fail (expected for some providers)
            # 429/5xx = retry
            if exc.code in (429, 500, 502, 503):
                if attempt < retries:
                    time.sleep(RETRY_DELAY)
                    continue
            return None
        except Exception:
            if attempt < retries:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


def fetch_text(url, timeout=HTTP_TIMEOUT):
    """Fetch a URL and return plain text with HTML tags stripped.

    Used to scrape provider documentation / change-log pages (CR #2).
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text


def try_provider_api(base_url):
    """Probe a provider's own ``/v1/models`` or ``/models`` endpoint.

    Returns a *set* of model IDs if the endpoint responds with data,
    or *None* if unavailable (auth required, 404, timeout, etc.).
    """
    for path in ("/v1/models", "/models"):
        data = _http_get_json(base_url.rstrip("/") + path, timeout=FAST_TIMEOUT, retries=0)
        if data:
            ids = set()
            for item in (data.get("data") or data.get("models") or []):
                if isinstance(item, dict):
                    val = item.get("id") or item.get("model") or item.get("name")
                    if val:
                        ids.add(str(val))
                else:
                    ids.add(str(item))
            if ids:
                return ids
    return None


# ──────────────────────────────────────────────────────────────────────────
# Dynamic rename discovery (CR #2: keep KNOWN_RENAMES in-sync automatically)
# ──────────────────────────────────────────────────────────────────────────

def discover_renames(provider):
    """Dynamically discover model renames by fetching provider docs/changelog.

    Returns a dict ``{old_name: new_name}`` (empty on failure).
    This augments ``KNOWN_RENAMES`` so the tool stays in-sync when providers
    introduce new deprecated model names — the list is not hardcoded-only.
    """
    url = RENAME_DOC_URLS.get(provider)
    if not url:
        return {}

    text = fetch_text(url, timeout=20)
    if not text:
        return {}

    if provider == "deepseek":
        # Parse the changelog for patterns like:
        #   "the legacy names deepseek-v4-flash and deepseek-v4-flash-vision-exp
        #    are still accepted, but the corresponding models have been retired;
        #    their requests are served by DeepSeek-V4.1-Flash-1017"
        renames = {}
        for m in re.finditer(
            r"(?:legacy\s+(?:model\s+)?names?)\s+(.+?)\s+"
            r"(?:are|have)\s+.*?retired",
            text, re.IGNORECASE | re.DOTALL,
        ):
            old_names = re.findall(
                r"deepseek-[a-z0-9._-]+", m.group(1), re.IGNORECASE
            )
            # Look for the replacement name after the "retired" mention
            after = text[m.end():m.end() + 600]
            repl = re.search(
                r"(?:served\s+by|replaced\s+by|superseded\s+by)\s+"
                r"([^\s.,;]+)",
                after, re.IGNORECASE,
            )
            if repl:
                new_name = repl.group(1).lower()
                for old in old_names:
                    renames[old.lower()] = new_name
        return renames

    # For Alibaba, the docs page shows example model IDs but not a full
    # rename mapping.  The fuzzy matching in verify_model handles the
    # rest.  Returns empty — callers fall back to KNOWN_RENAMES + fuzzy.
    return {}


# ──────────────────────────────────────────────────────────────────────────
# Source-specific fetchers
# ──────────────────────────────────────────────────────────────────────────

def fetch_openrouter_ids():
    """Fetch the full model list from OpenRouter's public API."""
    data = _http_get_json(OPENROUTER_MODELS_URL)
    if not data:
        return set()
    return {m["id"] for m in data.get("data", []) if m.get("id")}


def fetch_nvidia_ids():
    """Fetch the model list from NVIDIA's public endpoint (unauthenticated)."""
    data = _http_get_json(NVIDIA_MODELS_URL)
    if not data:
        return set()
    return {m.get("id", "") for m in data.get("data", []) if m.get("id")}


def crossref_from_openrouter(or_ids, provider):
    """Cross-reference a provider's models via OpenRouter.

    Strips the OpenRouter author prefix (e.g. ``deepseek/``) to get the
    bare model IDs that match the backup's naming convention.
    """
    prefix = CROSSREF_PREFIX.get(provider)
    if not prefix:
        return set()
    return {
        m[len(prefix):]
        for m in or_ids
        if m.startswith(prefix) and not m.startswith("~")
    }


def get_current_models(provider, base_url, or_ids, nv_ids, no_network=False):
    """Return (current_model_ids, source_description) for a provider.

    Strategy:
      1. Try the provider's own direct API (works for openrouter & nvidia).
      2. OpenRouter cross-reference for deepseek / alibaba / alibaba_eu.
      3. Empty set if nothing is available.
    """
    # 1 — Direct API (primary)
    direct = None if no_network else try_provider_api(base_url)
    if direct is not None:
        return direct, f"{provider} API ({base_url})"

    # 2 — OpenRouter cross-reference (fallback for auth-required providers)
    if provider in CROSSREF_PREFIX and or_ids:
        cross = crossref_from_openrouter(or_ids, provider)
        if cross:
            return cross, f"OpenRouter cross-reference ({CROSSREF_PREFIX[provider]}prefix)"

    # 3 — NVIDIA public API is a superset; useful for the nvidia provider
    #     even if the direct probe somehow failed.
    if provider == "nvidia" and nv_ids:
        return nv_ids, "NVIDIA public API (fallback)"

    return set(), f"no public source available for {provider}"


# ──────────────────────────────────────────────────────────────────────────
# Verification engine
# ──────────────────────────────────────────────────────────────────────────

def _strip_free(model_id):
    """Return (base_id, was_free_variant)."""
    if model_id.endswith(":free"):
        return model_id[:-5], True
    return model_id, False


def _strip_date_suffix(model_id):
    """Strip a trailing 4-digit date suffix (e.g. ``qwen3.8-max-0902`` → ``qwen3.8-max``)."""
    return re.sub(r"-[0-9]{4}$", "", model_id)


def _similarity(a, b):
    """Return a normalised similarity ratio in [0, 1]."""
    return SequenceMatcher(None, a, b).ratio()


def verify_model(model_id, provider, current_ids, source_desc, renames=None):
    """Classify a single backup model.

    Returns a dict: {"status", "new_model", "note"}
    Status is one of: current, renamed, deleted.

    *renames* — provider-specific rename map {old: new}.  Merges the
    hardcoded ``KNOWN_RENAMES`` with any entries discovered dynamically
    via ``discover_renames()``.
    """
    # 1 ── Known renames (highest priority — from provider changelogs) ──
    renames = renames or {}
    if model_id in renames:
        new = renames[model_id]
        return {
            "status": "renamed",
            "new_model": new,
            "note": (f"Documented rename: '{model_id}' → '{new}'. "
                     f"The legacy name is deprecated."),
        }

    # 2 ── Exact match ──────────────────────────────────────────────────
    if model_id in current_ids:
        return {
            "status": "current",
            "new_model": model_id,
            "note": f"Confirmed current via {source_desc}.",
        }

    # 3 ── ':free' variant discontinued — base model still exists ────────
    base, was_free = _strip_free(model_id)
    if was_free and base in current_ids:
        return {
            "status": "renamed",
            "new_model": base,
            "note": (f"The ':free' variant was discontinued; "
                     f"base model '{base}' is current."),
        }

    # 4 ── Dated snapshot (e.g. qwen3.8-max-0902 → qwen3.8-max) ─────────
    dated = _strip_date_suffix(model_id)
    if dated != model_id and dated in current_ids:
        return {
            "status": "renamed",
            "new_model": dated,
            "note": (f"Dated snapshot '{model_id}' has been consolidated "
                     f"to current '{dated}'."),
        }

    # 5 ── Fuzzy match (suggests the most likely rename) ────────────────
    #    Only suggest matches with a reasonably high similarity to avoid
    #    false positives across unrelated model families.
    matches = get_close_matches(model_id, current_ids, n=3, cutoff=FUZZY_CUTOFF)
    if matches:
        best = matches[0]
        score = _similarity(model_id, best)
        return {
            "status": "renamed",
            "new_model": best,
            "note": (f"No exact match found. Closest current model: "
                     f"'{best}' (similarity {score:.2f}). Verify before adopting."),
        }

    # 6 ── Deleted ──────────────────────────────────────────────────────
    return {
        "status": "deleted",
        "new_model": None,
        "note": (f"Not found in current model list ({source_desc}). "
                 f"No close match detected — model appears discontinued."),
    }


# ──────────────────────────────────────────────────────────────────────────
# Output formatters
# ──────────────────────────────────────────────────────────────────────────

def to_markdown(report):
    """Render the report as a Markdown document with actionable tables (CR #3)."""
    lines = []
    lines.append("# Model Verification Report")
    lines.append("")
    s = report["summary"]
    lines.append(f"**Source:** `{report['source_file']}`  ")
    lines.append(f"**Date:** {report['verification_date']}  ")
    lines.append(f"**Summary:** {s['total_models']} models | "
                 f"{s['current']} current | {s['renamed']} renamed | "
                 f"{s['deleted']} deleted")
    lines.append("")
    # Full results table
    lines.append("| # | Provider | Old Model | New Model | Status | Note |")
    lines.append("|---|----------|-----------|-----------|--------|------|")
    for i, r in enumerate(report["results"], 1):
        new = r["new_model"] if r["new_model"] else "—"
        lines.append(
            f"| {i} | {r['provider']} | `{r['old_model']}` | "
            f"`{new}` | {r['status']} | {r['note']} |"
        )
    lines.append("")
    # Action items for the second-step updater
    renamed = [r for r in report["results"] if r["status"] == "renamed"]
    deleted = [r for r in report["results"] if r["status"] == "deleted"]
    if renamed:
        lines.append("## Rename Actions (for the second-step updater)")
        lines.append("")
        lines.append("Replace these model IDs in `mods.yml`:")
        lines.append("")
        lines.append("| Provider | Old ID | New ID |")
        lines.append("|----------|--------|--------|")
        for r in renamed:
            new = r["new_model"] if r["new_model"] else "—"
            lines.append(f"| {r['provider']} | `{r['old_model']}` | `{new}` |")
        lines.append("")
    if deleted:
        lines.append("## Delete Actions (for the second-step updater)")
        lines.append("")
        lines.append("Remove these entries from `mods.yml`:")
        lines.append("")
        lines.append("| Provider | Old ID |")
        lines.append("|----------|--------|")
        for r in deleted:
            lines.append(f"| {r['provider']} | `{r['old_model']}` |")
        lines.append("")
    return "\n".join(lines)


def build_report(results, summary, backup_path):
    """Assemble the final report dict."""
    return {
        "verification_date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_file": str(backup_path),
        "summary": {
            "total_models": summary["total"],
            "current": summary["current"],
            "renamed": summary["renamed"],
            "deleted": summary["deleted"],
        },
        "results": results,
    }


def to_simple_yaml(report):
    """Hand-rolled YAML emitter (no external deps) for the report."""
    lines = []

    def emit(k, v, pad):
        if isinstance(v, bool):
            lines.append(f"{pad}{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{pad}{k}: null")
        elif isinstance(v, (int, float)):
            lines.append(f"{pad}{k}: {v}")
        elif isinstance(v, list):
            if not v:
                lines.append(f"{pad}{k}: []")
            else:
                lines.append(f"{pad}{k}:")
                for item in v:
                    s = str(item)
                    quote = any(c in s for c in [":", "#", "[", "]", "{", "}"])
                    lines.append(f"{pad}  - {json.dumps(s) if quote else s}")
        else:
            s = str(v)
            needs_quote = any(c in s for c in [":", "#", "{", "}", "[", "]", "&", "*"])
            lines.append(f"{pad}{k}: {json.dumps(s) if needs_quote else s}")

    # Header
    lines.append(f"# verification_date: {report['verification_date']}")
    lines.append(f"# source_file: {report['source_file']}")
    s = report["summary"]
    lines.append(f"# summary: {s['total_models']} total | "
                 f"{s['current']} current | {s['renamed']} renamed | "
                 f"{s['deleted']} deleted")
    lines.append("")
    lines.append("verifications:")
    for r in report["results"]:
        lines.append(f"  - provider: {r['provider']}")
        lines.append(f"    old_model: {r['old_model']}")
        emit("old_aliases", r["old_aliases"], "    ")
        emit("status", r["status"], "    ")
        emit("new_model", r["new_model"], "    ")
        emit("note", r["note"], "    ")
        lines.append("")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify models in a mods.yml backup against live provider APIs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python3 verify_models.py
  python3 verify_models.py mods.yml.bak.20261017-120406 --out report.json
  python3 verify_models.py --yaml --verbose
  python3 verify_models.py --md > report.md        # stdout = report only
  python3 verify_models.py "mods.yml.bak*"         # glob: newest match
""",
    )
    parser.add_argument("backup", nargs="?", default=None,
                        help="Path to the mods.yml backup file (supports globs; "
                             "default: auto-detect newest mods.yml.bak*)")
    parser.add_argument("--out", "-o", default=None,
                        help="Write report to this file (default: stdout)")
    parser.add_argument("--yaml", action="store_true",
                        help="Emit YAML output instead of JSON")
    parser.add_argument("--md", action="store_true",
                        help="Emit Markdown table output instead of JSON")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print per-model results (not just non-current ones)")
    parser.add_argument("--no-network", action="store_true",
                        help="Skip fetching live data (use only known renames)")
    args = parser.parse_args(argv)

    # ── Resolve backup file (supports glob patterns) ──
    backup_path = args.backup
    if backup_path is None:
        for candidate in CANDIDATE_BACKUPS:
            backup_path = resolve_backup(candidate)
            if backup_path:
                break
        if backup_path is None:
            say("Error: could not auto-detect a backup file. Specify one explicitly:")
            for c in CANDIDATE_BACKUPS:
                say(f"  {c}")
            return 2
    else:
        # User-provided path may contain glob wildcards (CR #1)
        backup_path = resolve_backup(args.backup)
        if backup_path is None:
            say(f"Error: no file matches '{args.backup}'")
            return 2

    say(f"[1/4] Parsing backup: {backup_path}")
    providers = parse_mods_yml(backup_path)
    total_models = sum(len(p["models"]) for p in providers.values())
    say(f"      → {len(providers)} providers, {total_models} models")

    if not providers:
        say("Error: no providers found in the 'apis:' section of the file.")
        return 2

    # ── Fetch live model lists ──
    say("[2/4] Fetching live model lists (public sources only)")
    if args.no_network:
        openrouter_ids = set()
        nvidia_ids = set()
        say("      → --no-network: skipping API calls")
    else:
        openrouter_ids = fetch_openrouter_ids()
        nvidia_ids = fetch_nvidia_ids()
        say(f"      → OpenRouter: {len(openrouter_ids)} models")
        say(f"      → NVIDIA:     {len(nvidia_ids)} models")
        if not openrouter_ids:
            say("      ⚠ Warning: OpenRouter API unavailable — "
                "DeepSeek/Alibaba cross-references will be empty.")

    # ── Discover dynamic renames from provider docs (CR #2) ──
    # Merge discovered renames into the hardcoded KNOWN_RENAMES so the
    # list stays in-sync when providers introduce new deprecated names.
    if not args.no_network:
        say("      Discovering renames from provider docs/changelogs ...")
        for prov in ("deepseek", "alibaba", "alibaba_eu"):
            dyn = discover_renames(prov)
            if dyn:
                KNOWN_RENAMES.setdefault(prov, {}).update(dyn)
                say(f"        {prov}: discovered {len(dyn)} additional rename(s)")

    # ── Verify each model ──
    say("[3/4] Verifying models")
    results = []
    summary = {"current": 0, "renamed": 0, "deleted": 0, "total": 0}

    for prov_name in providers:
        pinfo = providers[prov_name]
        base_url = pinfo.get("base-url", "")
        pmodels = pinfo["models"]
        if not pmodels:
            continue

        current_ids, source_desc = get_current_models(
            prov_name, base_url, openrouter_ids, nvidia_ids, args.no_network
        )
        say(f"      Provider: {prov_name:12s}  {len(pmodels):>3d} models  "
            f"(source: {source_desc})")

        prov_renames = KNOWN_RENAMES.get(prov_name, {})

        for model_id in sorted(pmodels):
            aliases = pmodels[model_id].get("aliases", [])
            outcome = verify_model(model_id, prov_name, current_ids, source_desc,
                                   renames=prov_renames)
            results.append({
                "provider": prov_name,
                "old_model": model_id,
                "old_aliases": aliases,
                "status": outcome["status"],
                "new_model": outcome["new_model"],
                "note": outcome["note"],
            })
            summary[outcome["status"]] += 1
            summary["total"] += 1

            if args.verbose or outcome["status"] != "current":
                tag = outcome["status"].upper()
                arrow = f" → {outcome['new_model']}" if outcome["new_model"] else ""
                say(f"        [{tag:8s}] {model_id}{arrow}")
                if outcome["status"] != "current":
                    say(f"                   {outcome['note']}")

    # ── Build & emit report ──
    say("[4/4] Building report")
    report = build_report(results, summary, backup_path)

    if args.md:
        output = to_markdown(report)
        fmt = "Markdown"
    elif args.yaml:
        output = to_simple_yaml(report)
        fmt = "YAML"
    else:
        output = json.dumps(report, indent=2, ensure_ascii=False)
        fmt = "JSON"

    if args.out:
        Path(args.out).write_text(output + "\n", encoding="utf-8")
        say(f"      → Report written to {args.out} ({fmt})")

    # Summary block goes to stderr so stdout stays clean for redirection
    s = report["summary"]
    say()
    say("=" * 72)
    say("  Model Verification Report")
    say(f"  Source:  {backup_path}")
    say(f"  Date:    {report['verification_date']}")
    say(f"  Summary: {s['total_models']} models | "
        f"{s['current']} current | {s['renamed']} renamed | {s['deleted']} deleted")
    say("=" * 72)

    # Only the report itself goes to stdout (clean for redirection)
    if args.out:
        say(f"\n  (Full {fmt} report written to {args.out})")
    else:
        print()
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
