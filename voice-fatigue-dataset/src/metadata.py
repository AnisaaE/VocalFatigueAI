from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.config import get_data_path

VIDEO_COLUMNS = [
    "video_id",
    "url",
    "title",
    "keyword_group",
    "keyword",
    "duration",
    "uploader",
    "upload_date",
    "has_subtitles",
    "subtitle_match_found",
    "downloaded_path",
    "candidate_type",
    "error",
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


def ensure_metadata_files() -> None:
    metadata_dir = get_data_path("metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)

    videos_csv = metadata_dir / "videos.csv"
    if not videos_csv.exists():
        pd.DataFrame(columns=VIDEO_COLUMNS).to_csv(videos_csv, index=False)

    segments_csv = metadata_dir / "segments.csv"
    if not segments_csv.exists():
        pd.DataFrame(columns=SEGMENT_COLUMNS).to_csv(segments_csv, index=False)


def load_videos_metadata() -> pd.DataFrame:
    path = get_data_path("metadata", "videos.csv")
    return pd.read_csv(path)


def save_videos_metadata(df: pd.DataFrame) -> None:
    path = get_data_path("metadata", "videos.csv")
    df.to_csv(path, index=False)


def append_video_record(record: dict) -> None:
    path = get_data_path("metadata", "videos.csv")
    df = pd.read_csv(path)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(path, index=False)


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
