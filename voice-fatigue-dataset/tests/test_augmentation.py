from pathlib import Path

import numpy as np

from src.augmentation import generate_augmented_dataset
from src.audio_utils import save_audio


def test_generate_augmented_dataset_creates_requested_counts(tmp_path: Path) -> None:
    input_root = tmp_path / "tired"
    output_root = tmp_path / "tired_augmented"
    sample_rate = 16000

    for speaker in ("anisa", "nalan"):
        speaker_dir = input_root / speaker
        speaker_dir.mkdir(parents=True, exist_ok=True)
        for idx in range(3):
            duration = 1.0
            t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
            sine = 0.05 * np.sin(2 * np.pi * (220 + idx * 20) * t)
            save_audio(sine.astype(np.float32), speaker_dir / f"{speaker}_{idx}.wav", sample_rate=sample_rate)

    total_saved = generate_augmented_dataset(
        input_root=input_root,
        output_root=output_root,
        speaker_counts={"anisa": 2, "nalan": 2},
        sample_rate=sample_rate,
        seed=7,
    )

    assert total_saved == 4
    assert len(list((output_root / "anisa").glob("*.wav"))) == 2
    assert len(list((output_root / "nalan").glob("*.wav"))) == 2
