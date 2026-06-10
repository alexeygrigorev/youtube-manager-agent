# youtube-manager-agent

Scripts for managing a YouTube channel from the command line: **download** a
long recording, **chop** it into per-lesson clips, **upload** or rename them with
proper metadata, organize them into **playlists** (at a chosen position), and add
**chapter** timecodes — all via the YouTube Data API v3.

Built for turning course/workshop recordings into a clean, playlist-organized set
of lesson videos, but the pieces are generic and work for any channel.

## What it can do

| Script | What it does |
|--------|--------------|
| `download.sh` | Download the best-quality source for a video (yt-dlp wrapper). |
| `chop.sh` | Cut a source video into clips from a `.spec` cut list, re-encoded with YouTube loudness normalization. |
| `clip_transcript.py` | Slice a source transcript into per-clip, clip-relative transcripts (for chapters) — no API needed. |
| `list_playlist.py` | Dump a playlist's items (`position  videoId  title`) so you can decide where to place a video. |
| `add_to_playlist.py` | Add videos to a playlist, or **move** an existing one — append, at a fixed `--position`, or `--before-title "…"`. Idempotent. |
| `rename.py` | Match manually-uploaded videos by filename and set title/description/tags/visibility + add to playlist (no upload audit needed). |
| `upload.py` | Full API upload from a manifest (requires an audited API project — see below). |
| `add_chapters.py` | Append chapter timecodes to each video's description. |

The chopping pipeline (download → spec → chop → captions/chapters) is documented
separately in [docs/chopping.md](docs/chopping.md).

## Install

This is a [uv](https://docs.astral.sh/uv/) project — the Google client libraries
are declared in `pyproject.toml`. Install them once:

```bash
uv sync
```

Then run any script with `uv run`:

```bash
uv run python list_playlist.py PLxxxxxxxx
```

`chop.sh` / `download.sh` additionally need `ffmpeg` and `yt-dlp` (the latter
runs via `uvx yt-dlp`, no install needed).

## Google Cloud setup (one time)

The API calls act on **your** channel, so you need your own OAuth credential.
You produce one file — `client_secret.json` — and the scripts cache a
`token.json` next to it after the first sign-in. Both live in the gitignored
`.youtube/` folder.

1. **Create/select a project** at the
   [Google Cloud Console](https://console.cloud.google.com).
2. **Enable the API:** *APIs & Services → Library →* search **"YouTube Data API
   v3"** → **Enable**. (This is the only API you need to activate.)
3. **OAuth consent screen:** choose **External**; fill in the app name/email.
   Under **Audience / Test users**, add the Google account that owns the channel.
   (Leaving the app in *Testing* is fine — test users can authorize it.)
4. **Create the credential:** *APIs & Services → Credentials → Create
   credentials → OAuth client ID →* Application type **Desktop app** → Create →
   **Download JSON**.
5. Save that file as **`.youtube/client_secret.json`** in this repo.

```
.youtube/
  client_secret.json   # you place this (from step 5)
  token.json           # created automatically on first run
  *-state.json         # per-manifest run state (created automatically)
```

### First run / scopes

The scripts request the `youtube` scope (read + write: needed for
`videos.insert/update` and playlist edits). The first command opens a browser
once for consent — you'll see *"Google hasn't verified this app" → Advanced → Go
to … (unsafe) → Allow*; that's expected for your own Desktop-app credential and
fine for these calls. After that, `token.json` (with a refresh token) is reused
with **no browser**.

> Windows tip: prefix a command with `PYTHONUTF8=1` so em dashes in titles print
> without a console encoding error.

## Typical workflows

### Place a video in a playlist at the right spot

Playlist **positions are 0-based** — position `0` is the first item, `1` the
second, and so on. List the playlist first to pick the slot:

```bash
# 1. See what's already in the playlist and at which positions
uv run python list_playlist.py PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv

# 2. Append it…
uv run python add_to_playlist.py --playlist PL3Mmux… https://youtu.be/7TuZTVwnmhk

# …or place it at a specific 0-based slot. If the video is already in the
#    playlist, this MOVES it there (otherwise it's inserted).
uv run python add_to_playlist.py --playlist PL3Mmux… --position 1 <id>

# …or before the first item with a given title prefix (inserts a group in order)
uv run python add_to_playlist.py --playlist PL3Mmux… --before-title "Module 4" <id1> <id2>
```

`add_to_playlist.py` accepts bare IDs or any watch/share URL, and is idempotent:
without `--position` an already-present video is skipped; with `--position` it's
repositioned.

### Publish chopped clips (recommended: manual upload + rename)

Videos uploaded **via the API** are locked to *private* until the API project
passes a one-time compliance audit. Editing metadata on videos **you** uploaded
has no such restriction, so the reliable path is:

1. Bulk drag-and-drop the clips into YouTube Studio. YouTube titles each draft
   after the filename (`module1-rag-l05-search.mp4` → `module1 rag l05 search`).
2. Run `rename.py` with a [manifest](manifests/) — it matches each entry by that
   default title, sets the real metadata, flips visibility to the manifest value,
   and adds it to the playlist:

```bash
uv run python rename.py --manifest manifests/part1-manifest.json --dry-run   # preview
uv run python rename.py --manifest manifests/part1-manifest.json             # apply
```

3. Add chapters once captions are ready:

```bash
uv run python add_chapters.py --manifest manifests/part1-manifest.json --chapters-dir work/chapters
```

`upload.py` does the whole thing through `videos.insert` instead — only useful
once your API project is **audited** (otherwise uploads stay private/draft).

## Manifests

A manifest holds, per video, the `file` (clip filename), `title`, and
`description`, plus global `privacyStatus`, `playlistId`, `tags`, `categoryId`,
`defaultLanguage`. `file` is only used to derive the match title (filename
without extension). See [`manifests/`](manifests/) for examples; copy and edit
per batch.

## Quota & cost

Default YouTube Data API quota is 10,000 units/day.
`videos.update` ≈ 50 units, `playlistItems.insert`/`update` ≈ 50, `videos.insert`
≈ 1,600 (so ~6 uploads/day). Renaming 10 videos is ~1,000 units.

## Security

Never commit `.youtube/` — it holds your `client_secret.json`, `token.json`, and
run state. Treat them like passwords. It's gitignored here.
