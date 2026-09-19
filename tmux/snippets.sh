#!/usr/bin/env bash
set -euo pipefail
FILE="${TMUX_SNIPPETS_FILE:-$HOME/.config/tmux/snippets.txt}"
pane="$1"   # tmux pane_id passed from the keybind

sel=$(fzf-tmux -p 80%,60% --reverse --prompt="snippet> " \
  --preview 'printf "%b" {}' --preview-window=down,3:wrap \
  < "$FILE") || exit 0

[[ -z "$sel" ]] && exit 0

# Paste into the originating pane. load-buffer/paste-buffer inserts the
# literal text (like a bracketed paste) instead of re-parsing it as
# keystrokes, so quotes/backticks/semicolons in a snippet are safe and
# nothing gets auto-submitted — you review before hitting Enter yourself.
printf '%b' "$sel" | tmux load-buffer -
tmux paste-buffer -t "$pane"

# Optional: also mirror it to the macOS system clipboard.
printf '%b' "$sel" | pbcopy
