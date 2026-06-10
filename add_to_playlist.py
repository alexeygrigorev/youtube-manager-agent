#!/usr/bin/env python3
"""Add or reposition videos in a playlist (idempotent).

Accepts bare video IDs or any watch/share URL. A video not yet in the playlist
is inserted; a video already present is left alone — UNLESS a position is given,
in which case it is moved there. Positions are 0-based (position 0 is the first
item in the playlist).

Place with an explicit `--position N`, or `--before-title "..."` to land before
the first existing item whose title starts with that text (handy for slotting a
group of videos into the middle of an ordered playlist).

  # append a video to the playlist
  python add_to_playlist.py --playlist PLxxxx https://youtu.be/7TuZTVwnmhk

  # put a video first (0-based), moving it if it's already in the playlist
  python add_to_playlist.py --playlist PLxxxx --position 0 <id>

  # insert several videos before the first item titled "Module 4 ..."
  python add_to_playlist.py --playlist PLxxxx --before-title "Module 4" id1 id2 id3
"""
import argparse
import re
import sys
from pathlib import Path

from googleapiclient.errors import HttpError

from auth import get_service


def video_id(s: str) -> str:
    """Accept a bare ID or any watch/share URL; return the 11-char video id."""
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})", s)
    return m.group(1) if m else s


def playlist_items(youtube, playlist_id: str):
    """Return [{position, videoId, title, itemId}, ...] for the whole playlist."""
    out, page = [], None
    while True:
        r = youtube.playlistItems().list(
            part="snippet", playlistId=playlist_id, maxResults=50, pageToken=page
        ).execute()
        for it in r.get("items", []):
            sn = it["snippet"]
            out.append({"position": sn["position"], "videoId": sn["resourceId"].get("videoId"),
                        "title": sn["title"], "itemId": it["id"]})
        page = r.get("nextPageToken")
        if not page:
            return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+", help="video IDs or watch URLs")
    ap.add_argument("--playlist", required=True, help="target playlist ID")
    ap.add_argument("--position", type=int, default=None,
                    help="0-based slot; inserts there, or MOVES the video if already present")
    ap.add_argument("--before-title", default=None,
                    help="place before the first item whose title starts with this")
    ap.add_argument("--client-secret", type=Path, default=None)
    ap.add_argument("--token", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    youtube = get_service(args.client_secret, args.token)

    current = playlist_items(youtube, args.playlist)
    by_vid = {it["videoId"]: it for it in current}

    pos = args.position
    if args.before_title is not None:
        match = next((it["position"] for it in current
                      if it["title"].startswith(args.before_title)), None)
        if match is None:
            print(f"No item titled '{args.before_title}*' — using end.", file=sys.stderr)
        pos = match

    for raw in args.videos:
        vid = video_id(raw)
        existing = by_vid.get(vid)

        if existing and pos is None:
            print(f"{vid}  already in playlist (pos {existing['position']}) — skipping")
            continue

        if existing:  # already present + position given -> move it
            if existing["position"] == pos:
                print(f"{vid}  already at position {pos} — skipping")
                continue
            print(f"{vid}  move {existing['position']} -> {pos}")
            if args.dry_run:
                continue
            try:
                youtube.playlistItems().update(part="snippet", body={
                    "id": existing["itemId"],
                    "snippet": {"playlistId": args.playlist, "position": pos,
                                "resourceId": {"kind": "youtube#video", "videoId": vid}},
                }).execute()
                print(f"  moved -> https://www.youtube.com/watch?v={vid}&list={args.playlist}")
            except HttpError as e:
                print(f"  ERROR: {e}", file=sys.stderr)
            continue

        # not present -> insert
        snippet = {"playlistId": args.playlist,
                   "resourceId": {"kind": "youtube#video", "videoId": vid}}
        if pos is not None:
            snippet["position"] = pos
        print(f"{vid}  insert {f'@ {pos}' if pos is not None else '(end)'}")
        if args.dry_run:
            continue
        try:
            youtube.playlistItems().insert(part="snippet", body={"snippet": snippet}).execute()
            print(f"  added -> https://www.youtube.com/watch?v={vid}&list={args.playlist}")
            if pos is not None:
                pos += 1
        except HttpError as e:
            print(f"  ERROR: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
