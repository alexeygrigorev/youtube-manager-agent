#!/usr/bin/env bash
# Copy the local OAuth token to a remote checkout of this repo.
#
# After re-authing here (`uv run python -m auth.reauth --force`), push the fresh
# token to a server that runs the same scripts headlessly.
#
# Usage: push_token.sh [host] [remote-repo-path]
#   push_token.sh                      # -> hetzner:~/git/youtube-manager-agent
#   push_token.sh hetzner ~/git/youtube-manager-agent
#   push_token.sh myserver /opt/youtube-manager-agent
set -euo pipefail

HOST="${1:-hetzner}"
REMOTE_DIR="${2:-~/git/youtube-manager-agent}"

# repo root is the parent of this script's bin/ dir
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOKEN="$ROOT/.youtube/token.json"

[ -f "$TOKEN" ] || { echo "no token at $TOKEN -- run 'uv run python -m auth.reauth' first" >&2; exit 1; }

ssh "$HOST" "mkdir -p $REMOTE_DIR/.youtube"
scp "$TOKEN" "$HOST:$REMOTE_DIR/.youtube/token.json"
echo "copied token -> $HOST:$REMOTE_DIR/.youtube/token.json"
