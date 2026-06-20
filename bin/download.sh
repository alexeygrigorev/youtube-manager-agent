#!/usr/bin/env bash
# Download the best-quality source for a YouTube video, for local chopping.
#
# YouTube tops out at 720p for many of these uploads, and a casual download often
# grabs the *lowest*-bitrate 720p (avc1 ~194 kb/s). This grabs the best stream at
# or below the height cap (vp9 720p ~336 kb/s + best audio) and merges to mkv.
#
# Usage: download.sh <video-url-or-id> [output-basename] [max-height]
#   download.sh https://www.youtube.com/watch?v=KSItlTAsMsk module1-rag 720
#
# Requires yt-dlp (run via `uvx yt-dlp` if not installed). Override the binary
# with YTDLP=/path/to/yt-dlp (default: "uvx yt-dlp").
set -euo pipefail

YTDLP="${YTDLP:-uvx yt-dlp}"
URL="$1"
NAME="${2:-%(title)s}"
MAXH="${3:-720}"

$YTDLP \
  -f "bv*[height<=${MAXH}]+ba/b[height<=${MAXH}]" \
  -S "res:${MAXH},br" \
  --merge-output-format mkv \
  -o "${NAME}.%(ext)s" \
  "$URL"
