from __future__ import annotations

import logging
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import soundfile as sf
import webrtcvad

from src.audio_utils import load_audio, save_audio
from src.metadata import append_segment_record, ensure_metadata_files
from src.config import load_config

logger = logging.getLogger(__name__)
Frame = namedtuple("Frame", ["bytes", "timestamp", "duration"])


def frame_generator(frame_duration_ms: int, audio: bytes, sample_rate: int) -> Iterable[Frame]:
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = frame_duration_ms / 1000.0
    while offset + n <= len(audio):
        chunk = audio[offset : offset + n]
        yield Frame(chunk, timestamp, duration)
        timestamp += duration
        offset += n


def is_speech(audio: np.ndarray, sample_rate: int, vad_mode: int = 3) -> bool:
    if audio.size == 0:
        return False
    pcm_data = (audio * 32767).astype(np.int16).tobytes()
    vad = webrtcvad.Vad(vad_mode)
    frames = list(frame_generator(30, pcm_data, sample_rate))
    if not frames:
        return False
    speech_count = sum(vad.is_speech(frame.bytes, sample_rate) for frame in frames)
    return speech_count / len(frames) >= 0.5


def split_fixed_segments(audio: np.ndarray, sample_rate: int, segment_duration: float) -> list[tuple[float, float, np.ndarray]]:
    segment_samples = int(segment_duration * sample_rate)
    results = []
    total_samples = audio.shape[0]
    for start_sample in range(0, total_samples, segment_samples):
        end_sample = min(start_sample + segment_samples, total_samples)
        segment = audio[start_sample:end_sample]
        start_time = start_sample / sample_rate
        end_time = end_sample / sample_rate
        results.append((start_time, end_time, segment))
    return results


def segment_audio_file(input_path: Path, output_dir: Path, sample_rate: int = 16000, segment_duration: int = 3) -> int:
    ensure_metadata_files()
    audio, sr = load_audio(input_path, sample_rate=sample_rate)
    segments = split_fixed_segments(audio, sr, segment_duration)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = 0

    for idx, (start_time, end_time, audio_chunk) in enumerate(segments, start=1):
        if not is_speech(audio_chunk, sr):
            continue
        filename = f"{input_path.stem}_{int(start_time*1000)}ms.wav"
        segment_path = output_dir / filename
        save_audio(audio_chunk, segment_path, sample_rate=sr)
        append_segment_record(
            source_audio=str(input_path),
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            sample_rate=sr,
            path=str(segment_path),
        )
        saved += 1
    logger.info("Saved %s speech segments from %s", saved, input_path.name)
    return saved


def segment_folder(input_dir: Path, output_dir: Path, config: dict | None = None) -> int:
    if config is None:
        config = load_config()
    segment_duration = config.get("segment_duration_seconds", 3)
    sample_rate = config.get("audio_sample_rate", 16000)

    audio_files = sorted(input_dir.glob("*.wav"))
    total_saved = 0
    for audio_path in audio_files:
        total_saved += segment_audio_file(audio_path, output_dir, sample_rate=sample_rate, segment_duration=segment_duration)
    return total_saved
