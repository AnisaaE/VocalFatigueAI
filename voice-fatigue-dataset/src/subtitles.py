from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Iterable

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def has_subtitles(video_info: dict) -> bool:
    return bool(video_info.get("subtitles") or video_info.get("automatic_captions"))


def download_subtitles(video_url: str, output_dir: Path) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_template = str(output_dir / "%(id)s.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "srt",
        "outtmpl": temp_template,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    video_id = info.get("id")
    if not video_id:
        return None

    candidate = output_dir / f"{video_id}.en.srt"
    if candidate.exists():
        return candidate

    candidate_alt = output_dir / f"{video_id}.srt"
    if candidate_alt.exists():
        return candidate_alt

    logger.debug("Subtitle download attempted for %s, path may not exist", video_id)
    return candidate if candidate.exists() else (candidate_alt if candidate_alt.exists() else None)


def parse_srt(srt_path: Path) -> list[dict[str, object]]:
    content = srt_path.read_text(encoding="utf-8", errors="ignore")
    entries = []
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        timestamp = lines[1].strip()
        text = " ".join(line.strip() for line in lines[2:] if line.strip())
        match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})", timestamp)
        if not match:
            continue
        start = _parse_timestamp(match.group(1))
        end = _parse_timestamp(match.group(2))
        entries.append({"start": start, "end": end, "text": text})
    return entries


def _parse_timestamp(value: str) -> float:
    hours, minutes, seconds_millis = value.split(":")
    seconds, millis = seconds_millis.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0


def _normalize_subtitle_text(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"[\[\]]", "", normalized)
    return normalized


def _flatten_keyword_groups(keyword_groups: dict[str, Iterable[str]]) -> list[tuple[str, str]]:
    flattened: list[tuple[str, str]] = []
    for category, keywords in keyword_groups.items():
        for keyword in keywords:
            flattened.append((category, keyword.lower()))
    return flattened


def find_matches(entries: Iterable[dict[str, object]], keyword_groups: dict[str, Iterable[str]]) -> list[dict[str, object]]:
    keywords = _flatten_keyword_groups(keyword_groups)
    matches: list[dict[str, object]] = []
    for entry in entries:
        text = _normalize_subtitle_text(str(entry.get("text", "")))
        for category, keyword in keywords:
            if keyword in text:
                matches.append(
                    {
                        "start": entry["start"],
                        "end": entry["end"],
                        "text": entry["text"],
                        "category": category,
                        "keyword": keyword,
                    }
                )
    return matches


def find_subtitle_match(srt_path: Path, keyword_groups: dict[str, Iterable[str]], threshold: int = 1) -> dict[str, object] | None:
    entries = parse_srt(srt_path)
    matches = find_matches(entries, keyword_groups)
    score = len(matches)
    if score < threshold:
        return None
    return {"score": score, "matches": matches, "first_match": matches[0]}
