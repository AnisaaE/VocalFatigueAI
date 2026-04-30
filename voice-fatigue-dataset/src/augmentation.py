from __future__ import annotations

import logging
import random
from pathlib import Path

import librosa
import numpy as np

from src.audio_utils import load_audio, save_audio

logger = logging.getLogger(__name__)


def _match_length(audio: np.ndarray, target_length: int) -> np.ndarray:
    if audio.shape[0] > target_length:
        return audio[:target_length]
    if audio.shape[0] < target_length:
        return np.pad(audio, (0, target_length - audio.shape[0]))
    return audio


def augment_audio(audio: np.ndarray, sample_rate: int, rng: random.Random) -> np.ndarray:
    augmented = np.copy(audio)

    if rng.random() < 0.7:
        gain = rng.uniform(0.9, 1.1)
        augmented = augmented * gain

    if rng.random() < 0.7:
        noise_scale = rng.uniform(0.001, 0.004)
        noise = np.random.default_rng(rng.randint(0, 1_000_000)).normal(0.0, noise_scale, size=augmented.shape)
        augmented = augmented + noise

    if rng.random() < 0.6:
        n_steps = rng.uniform(-0.6, 0.6)
        augmented = librosa.effects.pitch_shift(augmented, sr=sample_rate, n_steps=n_steps)

    if rng.random() < 0.6:
        rate = rng.uniform(0.94, 1.06)
        augmented = librosa.effects.time_stretch(augmented, rate=rate)

    augmented = _match_length(augmented, audio.shape[0])
    return np.clip(augmented, -1.0, 1.0).astype(np.float32)


def generate_augmented_dataset(
    input_root: Path,
    output_root: Path,
    speaker_counts: dict[str, int],
    sample_rate: int = 16000,
    seed: int = 42,
) -> int:
    rng = random.Random(seed)
    total_saved = 0

    for speaker, sample_count in speaker_counts.items():
        speaker_input_dir = input_root / speaker
        speaker_output_dir = output_root / speaker

        if not speaker_input_dir.exists():
            raise FileNotFoundError(f"Speaker directory not found: {speaker_input_dir}")

        source_files = sorted(speaker_input_dir.glob("*.wav"))
        if len(source_files) < sample_count:
            raise ValueError(
                f"Speaker '{speaker}' has only {len(source_files)} files, but {sample_count} were requested."
            )

        selected_files = rng.sample(source_files, sample_count)

        for index, source_path in enumerate(selected_files, start=1):
            audio, sr = load_audio(source_path, sample_rate=sample_rate)
            augmented = augment_audio(audio, sr, rng)
            output_name = f"{source_path.stem}_aug_{index:03d}.wav"
            save_audio(augmented, speaker_output_dir / output_name, sample_rate=sr)
            total_saved += 1

        logger.info("Generated %s augmented files for speaker '%s'", sample_count, speaker)

    logger.info("Generated %s augmented files in total", total_saved)
    return total_saved
