# Voice Fatigue Dataset Collector

A modular Python project for collecting and preparing candidate audio examples for a tired/normal voice classification dataset. The system automates YouTube search, candidate collection, subtitle-based candidate discovery, and fixed-length speech segmentation.

## What it does

- Searches YouTube with curated tired-voice keyword groups
- Collects candidate audio without assuming any label is correct
- Marks subtitle-based hits separately from keyword-only downloads
- Normalizes audio to WAV, mono, 16000 Hz
- Splits audio into fixed-length speech segments for manual review
- Stores metadata for videos and generated segments

## Important notes

- This pipeline gathers candidates only. Manual validation and labeling are required.
- Do not treat `data/candidates/` or `data/segments/unlabelled/` as true labels.
- Model splits should be performed by `video_id` or `speaker_id`, not by random segment sampling.
- `config.yaml` now supports separate subtitle matching keywords under `subtitle_match` and a minimum match threshold via `subtitle_score_threshold`.
- Subtitle text is normalized to match plain terms like `yawning` even when written as `[yawning]` in captions.

## Requirements

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

> Note: `pydub` and `yt-dlp` require `ffmpeg` available on PATH for audio processing.

## Project layout

```text
voice-fatigue-dataset/
  README.md
  requirements.txt
  config.yaml
  .gitignore

  data/
    raw/
      full_audio/
    candidates/
      keyword_only/
      subtitle_match/
    segments/
      subtitle_segments/
      unlabelled/
    labels/
      normal/
      tired/
      unsure/
    metadata/
      videos.csv
      segments.csv

  src/
    __init__.py
    main.py
    config.py
    youtube_search.py
    downloader.py
    subtitles.py
    audio_utils.py
    segmenter.py
    metadata.py
    cli.py

  tests/
    test_audio_utils.py
    test_segmenter.py
```

## Usage

Initialize folders and metadata files:

```bash
python -m src.cli init-folders
```

Collect candidate videos and audio:

```bash
python -m src.cli collect
```

Create unlabelled speech segments from keyword-only candidates:

```bash
python -m src.cli segment --input data/candidates/keyword_only --output data/segments/unlabelled
```

Create unlabelled speech segments from subtitle-match candidates:

```bash
python -m src.cli segment --input data/candidates/subtitle_match --output data/segments/unlabelled
```

## Metadata

- `data/metadata/videos.csv`: tracks `video_id`, `url`, `title`, `keyword_group`, `keyword`, and subtitle hit flags
- `data/metadata/segments.csv`: tracks extracted speech segments, source audio, timestamps, and review fields

## Machine learning guidance

- Data collected here are candidates, not labels.
- Manual review must assign `normal` or `tired` labels.
- Keep dataset splits by `video_id` or `speaker_id` to avoid leakage.
- Do not split randomly across individual segments.

## Testing

Run tests with:

```bash
pytest
```
