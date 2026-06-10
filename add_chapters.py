#!/usr/bin/env python3
"""Append generated chapter timecodes to each video's description.

Reads the manifest (base descriptions), the rename state (file -> videoId), and
a chapters file per video (chapters-dir/<short>.txt, where <short> is the part
of the filename from "l<NN>" on, e.g. l05-search). It rebuilds each description
as <base>\\n\\nChapters:\\n<lines> and pushes it via videos.update. Rebuilding
from the manifest base each run keeps it idempotent.

  python add_chapters.py --manifest manifests/part1-manifest.json \\
      --chapters-dir work/chapters [--dry-run]
"""
import argparse
import json
import re
from pathlib import Path

from googleapiclient.errors import HttpError

from auth import get_service, SECRETS_DIR


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def short_name(stem: str) -> str:
    m = re.search(r"l\d+.*$", stem)  # module1-rag-l05-search -> l05-search
    return m.group(0) if m else stem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--chapters-dir", type=Path, required=True)
    ap.add_argument("--state", type=Path, default=None,
                    help="rename state file (default: .youtube/<manifest-stem>-state.json)")
    ap.add_argument("--client-secret", type=Path, default=None)
    ap.add_argument("--token", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state_path = args.state or SECRETS_DIR / f"{args.manifest.stem}-state.json"
    cfg = load_json(args.manifest)
    state = load_json(state_path)
    yt = get_service(args.client_secret, args.token)
    tags = cfg.get("tags", [])

    for v in cfg["videos"]:
        f = v["file"]
        stem = Path(f).stem
        vid = state.get(f, {}).get("videoId")
        chap = args.chapters_dir / f"{short_name(stem)}.txt"
        if not vid:
            print(f"skip (no videoId in state): {f}"); continue
        if not chap.exists():
            print(f"skip (no chapters file): {chap}"); continue

        chapters = chap.read_text(encoding="utf-8").strip()
        desc = v["description"].rstrip() + "\n\nChapters:\n" + chapters + "\n"
        print(f"{v['title']}  ({vid})  [{len(chapters.splitlines())} chapters]")
        if args.dry_run:
            print("    " + chapters.replace("\n", "\n    ")); continue
        try:
            yt.videos().update(part="snippet", body={
                "id": vid,
                "snippet": {
                    "title": v["title"],
                    "description": desc,
                    "tags": tags,
                    "categoryId": cfg.get("categoryId", "27"),
                    "defaultLanguage": cfg.get("defaultLanguage", "en"),
                },
            }).execute()
            print("    chapters added")
        except HttpError as e:
            print(f"    ERROR: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
