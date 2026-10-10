#!/usr/bin/env bash
# ~/.config/tmux/dict-word.sh
# Fuzzy word search from system dictionary via fzf in a tmux popup.
# On selection, sends the word to the target pane via `tmux send-keys`.
#
# Usage (from tmux keybinding):
#   bind-key -T prefix g run-shell "~/.config/tmux/dict-word.sh '#{pane_id}'"
#
# Mnemonic: g = "get word" / "grep dictionary" / "grab word"

set -euo pipefail

TARGET_PANE="${1:?target pane id required}"
DICT_FILE="/usr/share/dict/words"

# Verify dictionary exists
[[ -r "$DICT_FILE" ]] || {
  tmux display-message "Dictionary not found: $DICT_FILE"
  exit 1
}

# Run fzf inside a tmux popup; on selection, pipe word to send-keys for target pane
tmux popup -E -w 60% -h 70% -T ' Dictionary (fzf) ' \
  "fzf --height=100% --reverse --prompt='Word> ' --border=rounded \
       --preview='echo {}' --preview-window=up:1:wrap \
       < '$DICT_FILE' | xargs -r tmux send-keys -t '$TARGET_PANE'"