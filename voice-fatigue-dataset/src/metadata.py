from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from src.config import get_data_path

VIDEO_COLUMNS = [
    "video_id",
    "url",
    "title",
    "keyword_group",
    "keyword",
    "has_subtitles",
    "subtitle_match_found",
]

SEGMENT_COLUMNS = [
    "segment_id",
    "source_audio",
    "start_time",
    "end_time",
    "duration",
    "sample_rate",
    "path",
    "manual_label",
    "speaker_id",
    "confidence",
    "notes",
]


def _parse_video_row(raw_line: str) -> list[str] | None:
    line = raw_line.strip()
    if not line:
        return None

    parsed = next(csv.reader([line]))
    if parsed == VIDEO_COLUMNS:
        return parsed
    if len(parsed) == len(VIDEO_COLUMNS):
        return parsed
    if len(parsed) < len(VIDEO_COLUMNS):
        parsed.extend([""] * (len(VIDEO_COLUMNS) - len(parsed)))
        return parsed

    # Legacy rows may contain unquoted commas in the title field.
    title = ",".join(parsed[2:-4]).strip()
    normalized = [
        parsed[0].strip(),
        parsed[1].strip(),
        title,
        parsed[-4].strip(),
        parsed[-3].strip(),
        parsed[-2].strip(),
        parsed[-1].strip(),
    ]
    return normalized


def _load_videos_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=VIDEO_COLUMNS)

    rows: list[list[str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw_line in handle:
            parsed = _parse_video_row(raw_line)
            if parsed is None:
                continue
            if parsed == VIDEO_COLUMNS:
                continue
            rows.append(parsed)

    return pd.DataFrame(rows, columns=VIDEO_COLUMNS)


def _save_videos_csv(df: pd.DataFrame, path: Path) -> None:
    df = df.reindex(columns=VIDEO_COLUMNS).fillna("")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def ensure_metadata_files() -> None:
    metadata_dir = get_data_path("metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)

    videos_csv = metadata_dir / "videos.csv"
    if not videos_csv.exists():
        pd.DataFrame(columns=VIDEO_COLUMNS).to_csv(videos_csv, index=False)
    else:
        _save_videos_csv(_load_videos_csv(videos_csv), videos_csv)

    segments_csv = metadata_dir / "segments.csv"
    if not segments_csv.exists():
        pd.DataFrame(columns=SEGMENT_COLUMNS).to_csv(segments_csv, index=False)


def load_videos_metadata() -> pd.DataFrame:
    path = get_data_path("metadata", "videos.csv")
    return _load_videos_csv(path)


def save_videos_metadata(df: pd.DataFrame) -> None:
    path = get_data_path("metadata", "videos.csv")
    _save_videos_csv(df, path)


def append_video_record(record: dict) -> None:
    path = get_data_path("metadata", "videos.csv")
    df = _load_videos_csv(path)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    _save_videos_csv(df, path)


def append_segment_record(source_audio: str, start_time: float, end_time: float, duration: float, sample_rate: int, path: str, manual_label: str = "", speaker_id: str = "", confidence: float = 1.0, notes: str = "") -> None:
    metadata_path = get_data_path("metadata", "segments.csv")
    df = pd.read_csv(metadata_path)
    segment_id = f"segment_{len(df) + 1:06d}"
    record = {
        "segment_id": segment_id,
        "source_audio": source_audio,
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "sample_rate": sample_rate,
        "path": path,
        "manual_label": manual_label,
        "speaker_id": speaker_id,
        "confidence": confidence,
        "notes": notes,
    }
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(metadata_path, index=False)
