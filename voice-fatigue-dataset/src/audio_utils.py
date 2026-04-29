from __future__ import annotations

import logging
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def ensure_wav_mono_16k(source_path: Path, target_path: Path) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(str(source_path))
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(str(target_path), format="wav")
    return target_path


def load_audio(path: Path, sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    data, sr = librosa.load(str(path), sr=sample_rate, mono=True)
    return data, sr


def save_audio(audio: np.ndarray, path: Path, sample_rate: int = 16000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sample_rate, subtype="PCM_16")
    return path


def normalize_audio_path(source_path: Path, target_path: Path, sample_rate: int = 16000) -> Path:
    return ensure_wav_mono_16k(source_path, target_path)
