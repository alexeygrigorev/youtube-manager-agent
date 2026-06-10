# Chopping long recordings into lesson clips

Turn a long recording (a live workshop, a webinar, a stream) into per-lesson
clips ready for upload, with frame-accurate cuts and YouTube loudness
normalization.

Working files live in the gitignored `work/` directory:

```
work/
  videos/        # source masters (downloaded) + chopped clips/
  transcripts/   # timestamped transcripts (per source)
  <name>.spec    # machine-readable cut list
captions/        # per-clip transcripts (for building chapters)
chapters/        # per-clip chapter timecodes
```

## Pipeline

### 1. Fetch a timestamped transcript
Pull it from YouTube (free, accurate) rather than transcribing locally:

```bash
python ~/.claude/skills/fetch-youtube/youtube.py <video-id> > work/transcripts/<name>.txt
```

Lines are `M:SS text` / `H:MM:SS text` — this is what the cut list is built from.

### 2. Get the best-quality source

```bash
bash download.sh "https://www.youtube.com/watch?v=<id>" work/videos/<name> 720
```

A casual download often grabs the *lowest*-bitrate 720p; `download.sh` selects
the best stream at or below the height cap and merges to mkv. (The true high-res
master is the original recording, not what YouTube re-encodes.)

### 3. Build the cut list (`<name>.spec`)
Read the transcript and map each lesson to timestamp ranges at **clean verbal
boundaries** (start of a sentence, not mid-word). One line per clip:

```
clipname|start1-end1[,start2-end2,...]      # integer seconds
```

Multiple comma-separated ranges are **concatenated** into one clip — use this to
drop an interruption from the middle of a lesson. Lines starting with `#` are
comments. Trim opening promos, logistics Q&A, filler ("I'll answer that later"),
dead air, and failed tangents; keep Q&A that is genuine lesson content. Clips
need not be contiguous, and a clip may come from a different position in the
source than its final course order.

### 4. Chop + normalize

```bash
bash chop.sh work/videos/<name>.mkv work/videos/clips <name>.spec <filename-prefix>
```

Each clip is re-encoded frame-accurate (`libx264 -preset faster -crf 23
-pix_fmt yuv420p`, audio `aac -b:a 192k`) with `loudnorm=I=-14:TP=-1.5:LRA=11`
(YouTube's normalization target) applied in the same pass. Override the binary
with `FFMPEG=/path/to/ffmpeg` if it isn't on `PATH`.

### 5. Iterate
To re-cut a lesson, edit its line in the `.spec` and re-run `chop.sh` (or
regenerate the single clip with a direct `ffmpeg` call). The spec is the source
of truth.

## Conventions

- **Naming:** `<prefix>-l<NN>-<slug>.mp4`, e.g. `module1-rag-l05-search.mp4`.
- **Loudness:** −14 LUFS, true peak −1.5 dBTP (YouTube target).
- **Output:** `work/videos/clips/` (gitignored).

## Gotchas

- **Never edit `chop.sh` while its batch is running.** Bash re-reads the script
  by byte offset as it executes; an edit shifts the offsets and can corrupt the
  run, clobbering already-finished clips. Let the batch finish, or regenerate
  individual clips with standalone `ffmpeg` calls. Editing the `.spec` mid-run
  is safe (the chopper already parsed it) — just re-run afterward.
- Re-encoding can't recover detail the source never had; for higher quality,
  start from the original recording, not a YouTube re-encode.

## Preparing chapter timecodes in advance

You don't have to wait for YouTube's ASR after upload. The source transcript is
already accurate and the spec records each clip's exact ranges, so slice the
transcript into per-clip, clip-relative captions right after chopping:

```bash
uv run python clip_transcript.py \
  --transcript work/transcripts/<name>.txt \
  --spec <name>.spec \
  --out-dir captions
```

It handles multi-segment clips (each kept segment shifted by the cumulative
duration of the ones before it). Turn `captions/<clip>.txt` into
`chapters/<clip>.txt` (`M:SS Title`, first line `0:00`, ≥3 entries, each ≥10s),
then inject them with `add_chapters.py`.
