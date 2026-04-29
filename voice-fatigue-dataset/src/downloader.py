from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from src.audio_utils import ensure_wav_mono_16k

logger = logging.getLogger(__name__)


def download_audio(video_url: str, output_path: Path) -> Path:
    """Download the video audio and ensure a normalized WAV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        logger.info("Skipping download, already exists: %s", output_path)
        return output_path

    temp_dir = output_path.parent / "_tmp_download"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_template = str(temp_dir / "%(id)s.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": temp_template,
        "nocheckcertificate": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    requested = info.get("requested_downloads") or []
    if requested:
        temp_file = Path(requested[0].get("filepath"))
    else:
        temp_file = temp_dir / f"{info.get('id')}.m4a"

    if not temp_file.exists():
        raise FileNotFoundError(f"Downloaded audio not found for {video_url}")

    ensure_wav_mono_16k(temp_file, output_path)
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        logger.warning("Could not remove temporary download directory: %s", temp_dir)
    return output_path
