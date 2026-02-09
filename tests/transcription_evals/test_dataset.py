from __future__ import annotations

from unittest.mock import Mock

import numpy as np
import pytest

from evals.transcription.src.core.dataset import to_wav_16k_mono


def test_to_wav_16k_mono_uses_cached_path(tmp_path, monkeypatch):
    cached = tmp_path / "cached.wav"
    cached.write_bytes(b"RIFFfake")

    example = {"audio": {"path": str(cached), "array": Mock(), "sampling_rate": 16000}}

    def _fail(*_args, **_kwargs):
        raise AssertionError("ffmpeg should not be invoked when cached path exists")

    monkeypatch.setattr("ffmpeg.input", _fail)
    monkeypatch.setattr("ffmpeg.output", _fail)
    monkeypatch.setattr("ffmpeg.run", _fail)

    assert to_wav_16k_mono(example, 0) == str(cached)


def test_to_wav_16k_mono_downmixes_stereo_and_returns_path(tmp_path, monkeypatch):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("evals.transcription.src.core.dataset.AUDIO_DIR", audio_dir)

    samples = np.array([[0.0, 1.0], [1.0, 0.0]])
    expected_mono = samples.mean(axis=1)

    captured = {}

    def fake_write(path, data, sr, subtype=None):  # noqa: ARG001
        captured["data"] = data

    monkeypatch.setattr("evals.transcription.src.core.dataset.sf.write", fake_write)
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.input", lambda *_: "input")
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.output", lambda *_args, **_kw: "output")
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.run", lambda *_args, **_kw: None)

    example = {"audio": {"array": samples, "sampling_rate": 16000}}
    output_path = to_wav_16k_mono(example, 1)

    assert output_path == str(audio_dir / "sample_000001.wav")
    np.testing.assert_allclose(captured["data"], expected_mono)


def test_to_wav_16k_mono_cleans_temp_on_ffmpeg_error(tmp_path, monkeypatch):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    monkeypatch.setattr("evals.transcription.src.core.dataset.AUDIO_DIR", audio_dir)

    temp_path_holder = {}

    def fake_write(path, data, sr, subtype=None):  # noqa: ARG001
        temp_path_holder["path"] = path

    def fake_run(*_args, **_kwargs):
        raise RuntimeError("ffmpeg failure")

    monkeypatch.setattr("evals.transcription.src.core.dataset.sf.write", fake_write)
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.input", lambda *_: "input")
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.output", lambda *_args, **_kw: "output")
    monkeypatch.setattr("evals.transcription.src.core.dataset.ffmpeg.run", fake_run)

    example = {"audio": {"array": np.zeros((2, 2)), "sampling_rate": 16000}}

    with pytest.raises(RuntimeError):
        to_wav_16k_mono(example, 2)

    temp_path = temp_path_holder["path"]
    assert temp_path is not None
    assert not temp_path.exists()
