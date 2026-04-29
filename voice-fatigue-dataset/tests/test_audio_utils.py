from pathlib import Path
import numpy as np
import soundfile as sf
from src.audio_utils import save_audio, load_audio


def test_save_and_load_audio(tmp_path: Path) -> None:
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    sine = 0.1 * np.sin(2 * np.pi * 440 * t)

    output_path = tmp_path / "test.wav"
    save_audio(sine, output_path, sample_rate=sample_rate)

    assert output_path.exists()
    data, sr = load_audio(output_path, sample_rate=sample_rate)
    assert sr == sample_rate
    assert data.shape[0] == sine.shape[0]
    assert np.isclose(data.max(), sine.max(), atol=1e-2)
