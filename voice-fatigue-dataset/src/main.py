from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from src.config import get_data_path, load_config
from src.downloader import download_audio
from src.metadata import append_video_record, ensure_metadata_files, load_videos_metadata
from src.segmenter import segment_folder
from src.subtitles import download_subtitles, find_subtitle_match, has_subtitles
from src.youtube_search import search_videos

logger = logging.getLogger(__name__)


def initialize_folders() -> None:
    ensure_metadata_files()
    get_data_path("raw", "full_audio").mkdir(parents=True, exist_ok=True)
    get_data_path("candidates", "keyword_only").mkdir(parents=True, exist_ok=True)
    get_data_path("candidates", "subtitle_match").mkdir(parents=True, exist_ok=True)
    get_data_path("segments", "subtitle_segments").mkdir(parents=True, exist_ok=True)
    get_data_path("segments", "unlabelled").mkdir(parents=True, exist_ok=True)
    get_data_path("labels", "normal").mkdir(parents=True, exist_ok=True)
    get_data_path("labels", "tired").mkdir(parents=True, exist_ok=True)
    get_data_path("labels", "unsure").mkdir(parents=True, exist_ok=True)
    logger.info("Project folder structure is initialized.")


def download_candidate_video(video_info: dict, subtitles_dir: Path, config: dict) -> dict:
    record = {
        "video_id": video_info.get("video_id"),
        "url": video_info.get("url"),
        "title": video_info.get("title"),
        "keyword_group": video_info.get("keyword_group"),
        "keyword": video_info.get("keyword"),
        "duration": video_info.get("duration"),
        "uploader": video_info.get("uploader"),
        "upload_date": video_info.get("upload_date"),
        "has_subtitles": False,
        "subtitle_match_found": False,
        "downloaded_path": "",
        "candidate_type": "keyword_only",
        "error": "",
    }

    try:
        info = search_single_video_info(video_info["url"])
        if has_subtitles(info):
            record["has_subtitles"] = True
            subtitle_path = download_subtitles(video_info["url"], subtitles_dir)
            if subtitle_path:
                threshold = int(config.get("subtitle_score_threshold", 1))
                subtitle_keywords = config.get("subtitle_match", {})
                match_info = find_subtitle_match(subtitle_path, subtitle_keywords, threshold)
                if match_info:
                    record["subtitle_match_found"] = True
                    record["candidate_type"] = "subtitle_match"
                    output_dir = get_data_path("candidates", "subtitle_match")
                    downloaded_path = output_dir / f"{video_info['video_id']}.wav"
                    download_audio(video_info["url"], downloaded_path)
                    record["downloaded_path"] = str(downloaded_path)
                    save_subtitle_segment(downloaded_path, match_info["first_match"], config)
                    return record
        output_dir = get_data_path("candidates", "keyword_only")
        downloaded_path = output_dir / f"{video_info['video_id']}.wav"
        download_audio(video_info["url"], downloaded_path)
        record["downloaded_path"] = str(downloaded_path)
        return record
    except Exception as exc:
        record["error"] = str(exc)
        logger.exception("Failed to download candidate audio for %s", video_info.get("video_id"))
        return record


def search_single_video_info(video_url: str) -> dict:
    from yt_dlp import YoutubeDL

    options = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(options) as ydl:
        return ydl.extract_info(video_url, download=False)


def save_subtitle_segment(full_audio_path: Path, match: dict, config: dict) -> None:
    from pydub import AudioSegment

    audio = AudioSegment.from_file(str(full_audio_path))
    start = max(0.0, float(match["start"]) - float(config.get("context_before_seconds", 1.5)))
    end = start + float(config.get("segment_duration_seconds", 3))
    if end > audio.duration_seconds:
        end = audio.duration_seconds
        start = max(0.0, end - float(config.get("segment_duration_seconds", 3)))
    excerpt = audio[start * 1000 : end * 1000]
    subtitle_dir = get_data_path("segments", "subtitle_segments")
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    segment_path = subtitle_dir / f"{full_audio_path.stem}_subtitle_{int(start*1000)}.wav"
    excerpt = excerpt.set_frame_rate(config.get("audio_sample_rate", 16000)).set_channels(config.get("audio_channels", 1))
    excerpt.export(str(segment_path), format="wav")


def collect_candidates() -> None:
    config = load_config()
    initialize_folders()
    subtitles_dir = get_data_path("raw", "full_audio")
    videos = search_videos(config)
    existing = load_videos_metadata()
    processed_ids = set(existing["video_id"].fillna(""))

    for video in tqdm(videos, desc="Collecting candidates", unit="video"):
        if video.get("video_id") in processed_ids:
            continue
        record = download_candidate_video(video, subtitles_dir, config)
        append_video_record(record)


def create_segments(input_dir: Path, output_dir: Path) -> None:
    config = load_config()
    initialize_folders()
    count = segment_folder(input_dir, output_dir, config)
    logger.info("Created %s segments from %s", count, input_dir)
