#!/usr/bin/env python3
"""Dump the items (position, videoId, title) of one or more playlists.

  python list_playlist.py PLxxxx [PLyyyy ...]
"""
import argparse
from pathlib import Path

from auth import get_service


def playlist_items(youtube, playlist_id: str):
    out, page = [], None
    while True:
        r = youtube.playlistItems().list(
            part="snippet", playlistId=playlist_id, maxResults=50, pageToken=page
        ).execute()
        for it in r.get("items", []):
            sn = it["snippet"]
            out.append((sn["position"], sn["resourceId"].get("videoId"), sn["title"]))
        page = r.get("nextPageToken")
        if not page:
            return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("playlists", nargs="+", help="playlist IDs")
    ap.add_argument("--client-secret", type=Path, default=None)
    ap.add_argument("--token", type=Path, default=None)
    args = ap.parse_args()

    youtube = get_service(args.client_secret, args.token)
    for pl in args.playlists:
        rows = playlist_items(youtube, pl)
        print(f"\n===== {pl}  ({len(rows)} items) =====")
        for pos, vid, title in rows:
            print(f"{pos:>3}  {vid}  {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
