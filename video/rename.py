#!/usr/bin/env python3
"""Fix metadata on videos you uploaded manually to YouTube Studio.

YouTube locks videos uploaded *via the API* to private until the API project
passes a one-time compliance audit. Editing metadata on videos you uploaded
yourself (videos.update) has no such restriction. So the reliable flow is:

  1. Bulk drag-and-drop the clips into YouTube Studio. YouTube names each draft
     after the file name (module1-rag-l05-search.mp4 -> "module1 rag l05 search").
  2. Run this script: it matches each manifest entry to the uploaded video by
     that default title (dash/space/case-insensitive), then sets the real
     title/description/tags/category, flips privacy to the manifest value, and
     adds the video to the playlist. Re-running is safe (state file + idempotent
     playlist add).

  python -m video.rename --manifest manifests/part1-manifest.json [--dry-run]
"""
import argparse
import json
import re
import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from auth.auth import get_service, SECRETS_DIR


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def norm(s: str) -> str:
    """Normalize a title for matching: YouTube turns filename dashes/underscores
    into spaces, so compare on lowercased alphanumerics separated by spaces."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def uploads_playlist_id(youtube) -> str:
    r = youtube.channels().list(part="contentDetails", mine=True).execute()
    return r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def list_uploaded_titles(youtube, uploads_pl: str) -> dict:
    """Return {normalized_title: videoId}, keeping the newest on collision."""
    out, page = {}, None
    while True:
        r = youtube.playlistItems().list(
            part="snippet", playlistId=uploads_pl, maxResults=50, pageToken=page
        ).execute()
        for it in r.get("items", []):
            sn = it["snippet"]
            key = norm(sn["title"])
            if key not in out:  # iterating newest-first, so keep the newest
                out[key] = sn["resourceId"]["videoId"]
        page = r.get("nextPageToken")
        if not page:
            return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--state", type=Path, default=None,
                    help="state file (default: .youtube/<manifest-stem>-state.json)")
    ap.add_argument("--client-secret", type=Path, default=None)
    ap.add_argument("--token", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true", help="match only, change nothing")
    args = ap.parse_args()

    state_path = args.state or SECRETS_DIR / f"{args.manifest.stem}-state.json"
    cfg = load_json(args.manifest)
    state = load_json(state_path)
    youtube = get_service(args.client_secret, args.token)

    uploads_pl = uploads_playlist_id(youtube)
    titles = list_uploaded_titles(youtube, uploads_pl)
    playlist_id = cfg.get("playlistId")
    tags = cfg.get("tags", [])

    for v in cfg["videos"]:
        stem = Path(v["file"]).stem  # default title YouTube assigns on upload
        vid = state.get(v["file"], {}).get("videoId") or titles.get(norm(stem))
        if not vid:
            print(f"NO MATCH for '{stem}' — upload {v['file']} first, or rename its "
                  f"default title to '{stem}'.", file=sys.stderr)
            continue

        print(f"{v['title']}  <-  {stem}  ({vid})")
        if args.dry_run:
            continue

        rec = state.get(v["file"], {"videoId": vid})
        try:
            youtube.videos().update(part="snippet,status", body={
                "id": vid,
                "snippet": {
                    "title": v["title"],
                    "description": v["description"],
                    "tags": tags,
                    "categoryId": cfg.get("categoryId", "27"),
                    "defaultLanguage": cfg.get("defaultLanguage", "en"),
                },
                "status": {"privacyStatus": cfg.get("privacyStatus", "unlisted")},
            }).execute()
            rec["updated"] = True

            if playlist_id and not rec.get("inPlaylist"):
                youtube.playlistItems().insert(part="snippet", body={"snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": vid},
                }}).execute()
                rec["inPlaylist"] = True

            state[v["file"]] = rec
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"  updated + playlisted -> https://youtu.be/{vid}")
        except HttpError as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
