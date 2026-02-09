from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from evals.transcription.src.adapters.azure import AzureSTTAdapter
from evals.transcription.src.adapters.whisper import WhisperAdapter
from evals.transcription.src.core.dataset import to_wav_16k_mono
from evals.transcription.src.core.metrics import compute_wer_metrics, compute_wer_pct, normalise_text
from evals.transcription.src.core.runner import run_engines_parallel
from evals.transcription.src.evaluate import run_evaluation


class FakeAdapter:
    def __init__(self, label: str, hyp: str, proc_sec: float = 0.25):
        self.label = label
        self.hyp = hyp
        self.proc_sec = proc_sec

    def transcribe(self, wav_path: str):  # noqa: ARG002
        return self.hyp, self.proc_sec, {"label": self.label}


class FakeDataset:
    def __init__(self, samples: list[dict]):
        self._samples = samples

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int) -> dict:
        return self._samples[idx]


def test_normalise_text_edge_cases():
    assert normalise_text("") == ""
    assert normalise_text("  Hello,   WORLD!!  ") == "hello world"


def test_compute_wer_metrics_empty_inputs():
    metrics = compute_wer_metrics([], [])
    assert metrics["wer"] == 0.0
    assert metrics["hits"] == 0
    assert compute_wer_pct([], []) == 0.0


def test_compute_wer_metrics_small_example():
    metrics = compute_wer_metrics(["hello world"], ["hello there world"])
    assert metrics["insertions"] == 1
    assert metrics["deletions"] == 0
    assert metrics["substitutions"] == 0


def test_run_evaluation_with_fake_adapters(monkeypatch):
    samples = [
        {"text": "hello world", "audio": {"path": "/tmp/a.wav"}},
        {"text": "good morning", "audio": {"path": "/tmp/b.wav"}},
    ]
    dataset = FakeDataset(samples)

    fake_settings = SimpleNamespace(AZURE_SPEECH_KEY="key", AZURE_SPEECH_REGION="region")
    monkeypatch.setattr("evals.transcription.src.evaluate.settings", fake_settings)
    monkeypatch.setattr("evals.transcription.src.evaluate.load_benchmark_dataset", lambda **_: dataset)
    monkeypatch.setattr("evals.transcription.src.evaluate.to_wav_16k_mono", lambda ex, idx: ex["audio"]["path"])
    monkeypatch.setattr("evals.transcription.src.evaluate.audio_duration_seconds", lambda _: 1.0)

    monkeypatch.setattr(
        "evals.transcription.src.evaluate.AzureSTTAdapter",
        lambda **_: FakeAdapter("Azure Speech-to-Text", "hello world"),
    )
    monkeypatch.setattr(
        "evals.transcription.src.evaluate.WhisperAdapter",
        lambda **_: FakeAdapter("Whisper", "good morning"),
    )

    captured = {}

    def fake_save_results(results, output_path):
        captured["results"] = results
        captured["output_path"] = output_path

    monkeypatch.setattr("evals.transcription.src.evaluate.save_results", fake_save_results)

    run_evaluation(num_samples=2)

    results = captured["results"]
    assert len(results) == 2
    assert {r["summary"]["engine"] for r in results} == {"Azure Speech-to-Text", "Whisper"}

    for result in results:
        summary = result["summary"]
        assert summary["num_samples"] == 2
        assert summary["overall_wer_pct"] >= 0.0
        samples_out = result["samples"]
        assert [s["dataset_index"] for s in samples_out] == [0, 1]
        assert all("engine_debug" in s for s in samples_out)


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


def test_run_engines_parallel_bookkeeping():
    dataset = FakeDataset(
        [
            {"text": "hello world", "audio": {"path": "/tmp/a.wav"}},
            {"text": "good night", "audio": {"path": "/tmp/b.wav"}},
        ]
    )

    adapters_config = [
        {"adapter": FakeAdapter("A", "hello world", proc_sec=0.5), "label": "Adapter A"}
    ]

    results = run_engines_parallel(
        adapters_config=adapters_config,
        indices=[0, 1],
        dataset=dataset,
        wav_write_fn=lambda ex, idx: ex["audio"]["path"],
        duration_fn=lambda _path: 2.0,
    )

    assert len(results) == 1
    summary = results[0]["summary"]
    assert summary["engine"] == "Adapter A"
    assert summary["num_samples"] == 2
    assert summary["process_sec"] == pytest.approx(1.0)
    assert summary["audio_sec"] == pytest.approx(4.0)
    assert summary["rtf"] == pytest.approx(0.25)

    samples_out = results[0]["samples"]
    assert samples_out[0]["dataset_index"] == 0
    assert samples_out[1]["dataset_index"] == 1
    assert samples_out[0]["engine"] == "Adapter A"
    assert samples_out[0]["rtf"] == pytest.approx(0.25)


def test_adapter_contracts(monkeypatch):
    async def fake_start(_path):
        return SimpleNamespace(transcript=[{"text": "hello"}, {"text": "world"}])

    monkeypatch.setattr(
        "evals.transcription.src.adapters.azure.CommonAzureAdapter.start", fake_start
    )
    monkeypatch.setattr(
        "evals.transcription.src.adapters.whisper.WhisplyLocalAdapter.start", fake_start
    )

    azure = AzureSTTAdapter("key", "region")
    text, proc_sec, debug = azure.transcribe("/tmp/a.wav")
    assert isinstance(text, str)
    assert isinstance(proc_sec, float)
    assert isinstance(debug, dict)

    whisper = WhisperAdapter(model_name="small", language="en")
    text, proc_sec, debug = whisper.transcribe("/tmp/b.wav")
    assert isinstance(text, str)
    assert isinstance(proc_sec, float)
    assert isinstance(debug, dict)


def test_run_evaluation_requires_azure_credentials(monkeypatch):
    dataset = FakeDataset([])
    fake_settings = SimpleNamespace(AZURE_SPEECH_KEY=None, AZURE_SPEECH_REGION=None)

    monkeypatch.setattr("evals.transcription.src.evaluate.settings", fake_settings)
    monkeypatch.setattr("evals.transcription.src.evaluate.load_benchmark_dataset", lambda **_: dataset)

    with pytest.raises(ValueError, match="Azure credentials not found"):
        run_evaluation(num_samples=1)
