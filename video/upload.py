#!/usr/bin/env python3
"""Upload local video files to YouTube from a manifest, add them to a playlist.

NOTE: videos uploaded via the API are locked to *private* until the API project
passes a one-time compliance audit. If your project is unaudited, prefer the
manual-upload + rename.py flow (see README). This script is the end-to-end path
once your project is audited.

  python -m video.upload --manifest manifests/part1-manifest.json --videos-dir work/clips

State is written to .youtube/<manifest-stem>-upload-state.json so re-running
skips already-uploaded clips (useful if the daily upload quota is hit).
"""
import argparse
import json
import sys
import time
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from auth.auth import get_service, SECRETS_DIR


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def upload_one(youtube, path: Path, snippet: dict, status: dict) -> str:
    body = {"snippet": snippet, "status": status}
    media = MediaFileUpload(str(path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]


def add_to_playlist(youtube, playlist_id: str, video_id: str):
    youtube.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": playlist_id,
        "resourceId": {"kind": "youtube#video", "videoId": video_id},
    }}).execute()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--videos-dir", type=Path, required=True)
    ap.add_argument("--state", type=Path, default=None,
                    help="state file (default: .youtube/<manifest-stem>-upload-state.json)")
    ap.add_argument("--client-secret", type=Path, default=None)
    ap.add_argument("--token", type=Path, default=None)
    args = ap.parse_args()

    state_path = args.state or SECRETS_DIR / f"{args.manifest.stem}-upload-state.json"
    cfg = load_json(args.manifest)
    state = load_json(state_path)  # {filename: {"videoId":..., "inPlaylist":bool}}
    youtube = get_service(args.client_secret, args.token)

    tags = cfg.get("tags", [])
    playlist_id = cfg.get("playlistId")

    for v in cfg["videos"]:
        fname = v["file"]
        path = (args.videos_dir / fname).resolve()
        rec = state.get(fname, {})

        if not path.exists():
            print(f"SKIP (missing file): {fname}", file=sys.stderr)
            continue

        try:
            if not rec.get("videoId"):
                snippet = {
                    "title": v["title"],
                    "description": v["description"],
                    "tags": tags,
                    "categoryId": cfg.get("categoryId", "27"),
                    "defaultLanguage": cfg.get("defaultLanguage", "en"),
                }
                status = {"privacyStatus": cfg.get("privacyStatus", "unlisted"),
                          "selfDeclaredMadeForKids": False}
                print(f"Uploading: {v['title']} ...", flush=True)
                vid = upload_one(youtube, path, snippet, status)
                rec["videoId"] = vid
                rec["inPlaylist"] = False
                state[fname] = rec
                state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
                print(f"  uploaded -> https://youtu.be/{vid}", flush=True)
            else:
                print(f"already uploaded: {v['title']} -> https://youtu.be/{rec['videoId']}")

            if playlist_id and not rec.get("inPlaylist"):
                add_to_playlist(youtube, playlist_id, rec["videoId"])
                rec["inPlaylist"] = True
                state[fname] = rec
                state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
                print("  added to playlist", flush=True)

        except HttpError as e:
            msg = str(e)
            if "quotaExceeded" in msg or "uploadLimitExceeded" in msg:
                print(f"\nQuota/upload limit reached. Progress saved to "
                      f"{state_path}. Re-run tomorrow to continue.", file=sys.stderr)
                return 2
            print(f"ERROR on {fname}: {msg}", file=sys.stderr)
            time.sleep(2)

    done = sum(1 for r in state.values() if r.get("videoId"))
    print(f"\nDone. {done}/{len(cfg['videos'])} uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
