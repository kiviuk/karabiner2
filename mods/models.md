# @mods.yml — Model Reference

> Auto-generated from @mods.yml. Each model configured with API, description, and recommended usage.

---

## DeepSeek API

| Model | Description | Best Usage |
|---|---|---|
| `deepseek-v4-pro` | DeepSeek V4 Pro — 1.6T MoE with 49B active params, 1M context | Complex reasoning, long-document analysis, agentic workflows |
| `deepseek-v4-flash` | DeepSeek V4 Flash — 284B MoE with 13B active params, 1M context | Fast, efficient coding and everyday tasks (cheaper than Pro) |

---

## NVIDIA NIM API

| Model | Description | Best Usage |
|---|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | Nemotron 3 Ultra — 55B active / 550B total, frontier reasoning | Best available reasoning, complex agents, long-horizon tasks |
| `nvidia/nemotron-3-super-120b-a12b` | Nemotron 3 Super — 12B active / 120B total MoE | Strong general-purpose, balanced quality/speed |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Nemotron 3 Nano Omni — multimodal, 30B-A3B | Vision + reasoning, image understanding with inference |
| `nvidia/nemotron-3.5-lightning-30b-a3b` | Nemotron 3.5 Lightning — 3B active / 30B total MoE | High-throughput, fast responses, batch workloads |
| `nvidia/llama-3.1-nemotron-ultra-253b-v1` | Llama-Nemotron Ultra — 253B dense | Dense alternative to Nemotron Ultra, strong reasoning |
| `nvidia/llama-3.1-nemotron-70b-instruct` | Llama-Nemotron 70B — dense 70B | Strong 70B general-purpose, reliable all-rounder |
| `nvidia/nemotron-4-340b-instruct` | Nemotron 4 — latest generation | Newer Nemotron line, general improvement over v3 |
| `nvidia/llama-3.1-nemoguard-8b-content-safety` | Nemoguard — 4B content moderation | Input/output safety filtering, content moderation |
| `google/gemma-4-31b-it` | Gemma 4 31B — Google dense multimodal | Multimodal tasks, Google ecosystem, balanced performance |
| `z-ai/glm-5.3` | GLM 5.3 — Z.ai flagship, 1.3M context | Complex coding, long-horizon agent tasks, software engineering |
| `moonshotai/kimi-k3` | Kimi K3 — 2.8T MoE multimodal | Moonshot flagship, multimodal, complex reasoning |
| `moonshotai/kimi-k2.6` | Kimi K2.6 — Moonshot coding specialist | Coding-focused tasks, UI/UX generation from code |

---

## Alibaba DashScope (International)

| Model | Description | Best Usage |
|---|---|---|
| `qwen3.8-plus` | Qwen 3.8 Plus — hybrid MoE, balanced tier | General-purpose, balanced quality/cost (1M context) |
| `qwen3.8-max-0902` | Qwen 3.8 Max — 2.4T sparse MoE, 95B active | Flagship, strongest Qwen capability, complex tasks |
| `qwen3.8-flash` | Qwen 3.8 Flash — fast and efficient | Fast responses, high-volume, cost-sensitive workloads |
| `qwen3.8-27b` | Qwen 3.8 27B — dense vision-language | Multimodal, vision-language, dense model at 27B |
| `qwen3.8-27b:free` | Qwen 3.8 27B — **free tier** (256K context) | **Free** — budget-friendly dense multimodal model |

---

## Alibaba DashScope (EU)

> Same models as International, served from EU (Frankfurt) region.

| Model | Description | Best Usage |
|---|---|---|
| `qwen3.8-plus` | Qwen 3.8 Plus — hybrid MoE, balanced tier | General-purpose, balanced quality/cost (1M context) |
| `qwen3.8-max-0902` | Qwen 3.8 Max — 2.4T sparse MoE, 95B active | Flagship, strongest Qwen capability, complex tasks |
| `qwen3.8-flash` | Qwen 3.8 Flash — fast and efficient | Fast responses, high-volume, cost-sensitive workloads |
| `qwen3.8-27b` | Qwen 3.8 27B — dense vision-language | Multimodal, vision-language, dense model at 27B |
| `qwen3.8-27b:free` | Qwen 3.8 27B — **free tier** (256K context) | **Free** — budget-friendly dense multimodal model |

---

## OpenRouter

| Model | Description | Best Usage |
|---|---|---|
| `deepseek/deepseek-v3.2` | DeepSeek V3.2 — 160K context, strong general | General coding, reasoning, everyday tasks |
| `deepseek/deepseek-v3.2-exp` | DeepSeek V3.2 Exp — experimental variant | Experimental features, testing new capabilities |
| `openai/gpt-4o-mini` | GPT-4o mini — OpenAI's smallest multimodal | Fast, affordable, great for simple tasks and chat |
| `openai/gpt-5.4` | GPT-5.4 — OpenAI frontier model | State-of-the-art reasoning, coding, multimodal (1M context) |
| `xiaomi/mimo-v2.5` | MiMo-V2.5 — Xiaomi native omnimodal | Vision-language tasks, agentic reasoning (1M context) |
| `nvidia/nemotron-3-nano-30b-a3b` | Nemotron 3 Nano — NVIDIA efficient MoE | NVIDIA-hosted, efficient reasoning, fast responses |
| `minimax/minimax-m2.5` | MiniMax M2.5 — strong general purpose | Good all-rounder from MiniMax (200K context) |
| `minimax/minimax-m2.7` | MiniMax M2.7 — next-gen MiniMax | Improved MiniMax, better reasoning and coding |
| `z-ai/glm-5` | GLM 5 — Z.ai flagship open model | Z.ai's flagship, agentic workflows (200K context) |
| `moonshotai/kimi-k3` | Kimi K3 — Moonshot multimodal flagship | Moonshot's best model, multimodal, long context (1M) |
| `anthropic/claude-opus-4.8` | Claude Opus 4.8 — Anthropic's strongest | Anthropic flagship, coding, long-running professional tasks (1M) |
| `xiaomi/mimo-v2.5-pro` | MiMo-V2.5-Pro — Xiaomi premium | Premium Xiaomi model, agentic performance (1M context) |
| `kwaipilot/kat-coder-pro-v2.5` | KAT-Coder-Pro V2.5 — coding specialist | Enterprise-grade coding, complex software engineering |
| `qwen/qwen3.6-plus` | Qwen 3.6 Plus — Alibaba balanced MoE | Balanced Qwen, general-purpose (1M context) |
| `qwen/qwen3-coder` | Qwen3 Coder — 480B A35B coding MoE | Specialized code generation, programming tasks |
| `cohere/north-mini-code:free` | North Mini Code — Cohere agentic coding | **Free** — coding tasks, agentic workflows (256K) |
| `poolside/laguna-s-2.1:free` | Laguna S 2.1 — Poolside coding agent | **Free** — coding agent, software engineering (256K) |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | Nemotron 3 Ultra — NVIDIA frontier | **Free** — frontier reasoning, best free option (1M) |
| `thinkingmachines/inkling:free` | Inkling — TM Lab multimodal MoE | **Free** — multimodal reasoning, complex tasks (1M) |
| `nvidia/nemotron-3-super-120b-a12b:free` | Nemotron 3 Super — NVIDIA large MoE | **Free** — strong general-purpose, large MoE (256K) |
| `z-ai/glm-5.2:free` | GLM 5.2 — Z.ai reasoning | **Free** — reasoning model ⚠️ 32K context only (very short) |

---

## Default Model

| Model | API | Description |
|---|---|---|
| `v4` → `deepseek-v4-pro` | DeepSeek | Default fast chat model — 1M context, strong general/coding |

---

## Summary by Cost

| Tier | Models |
|---|---|
| **Free** | `cohere/north-mini-code:free`, `poolside/laguna-s-2.1:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `thinkingmachines/inkling:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `z-ai/glm-5.2:free`, `qwen3.8-27b:free` (Alibaba + EU) |
| **Paid — Fast/Efficient** | `deepseek-v4-flash`, `openai/gpt-4o-mini`, `qwen3.8-flash`, `nvidia/nemotron-3.5-lightning-30b-a3b` |
| **Paid — Balanced** | `deepseek-v4-pro`, `openai/gpt-5.4`, `xiaomi/mimo-v2.5`, `minimax-m2.5/2.7`, `z-ai/glm-5`, `moonshotai/kimi-k3`, `anthropic/claude-opus-4.8`, `qwen3.8-plus`, `qwen/qwen3.6-plus`, `z-ai/glm-5.3` |
| **Paid — Flagship** | `moonshotai/kimi-k2.6`, `qwen3.8-max-0902`, `nvidia/nemotron-3-ultra-550b-a55b`, `nvidia/llama-3.1-nemotron-ultra-253b-v1`, `xiaomi/mimo-v2.5-pro`, `kwaipilot/kat-coder-pro-v2.5`, `qwen/qwen3-coder` |
| **Specialized** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` (vision), `nvidia/llama-3.1-nemotron-70b-instruct` (70B), `nvidia/nemotron-4-340b-instruct` (Nemotron 4), `nvidia/llama-3.1-nemoguard-8b-content-safety` (safety), `google/gemma-4-31b-it` (Google), `deepseek/deepseek-v3.2` / `deepseek/deepseek-v3.2-exp` (V3.2 family) |

---

## ⚠️ Known Limitations

| Model | Issue |
|---|---|
| `z-ai/glm-5.2:free` | **Only 32K context** — extremely short for a "1M" model. Don't use for long documents. |
| `nvidia/nemotron-3-ultra-550b-a55b` | NIM API returns 262K (not 1M). OpenRouter free version supports 1M. |
| `nvidia/nemotron-3-ultra-550b-a55b:free` | Free tier availability may vary — verify on OpenRouter. |
| `nvidia/nemotron-4-340b-instruct` | Context length unverified (set to 128K as estimate). |
| `qwen/qwen3-coder` | Context 262K — lower than other Qwen 3.8 models (1M). |
