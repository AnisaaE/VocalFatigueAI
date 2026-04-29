from pathlib import Path
import numpy as np
import soundfile as sf
import webrtcvad
from src.segmenter import segment_audio_file


def test_segment_audio_file_creates_segments(tmp_path: Path, monkeypatch) -> None:
    sample_rate = 16000
    duration = 5.0
    t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False)
    audio = 0.02 * np.sin(2 * np.pi * 440 * t)

    input_path = tmp_path / "input.wav"
    sf.write(str(input_path), audio, sample_rate, subtype="PCM_16")

    output_dir = tmp_path / "segments"
    monkeypatch.setattr(webrtcvad.Vad, "is_speech", lambda self, frame, sample_rate: True)

    count = segment_audio_file(input_path, output_dir, sample_rate=sample_rate, segment_duration=2)
    assert count == 3
    saved_files = list(output_dir.glob("*.wav"))
    assert len(saved_files) == 3
    for path in saved_files:
        data, sr = sf.read(str(path))
        assert sr == sample_rate
        assert data.size > 0
