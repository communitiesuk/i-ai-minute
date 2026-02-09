from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import soundfile as sf

from evals.transcription.src.adapters.azure import AzureSTTAdapter
from evals.transcription.src.adapters.whisper import WhisperAdapter
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


def test_run_evaluation_with_fake_adapters(tmp_path, monkeypatch):
    wav_a = tmp_path / "a.wav"
    wav_b = tmp_path / "b.wav"
    sf.write(wav_a, [0.0, 0.0], 16000, subtype="PCM_16")
    sf.write(wav_b, [0.0, 0.0], 16000, subtype="PCM_16")

    samples = [
        {"text": "hello world", "audio": {"path": str(wav_a)}},
        {"text": "good morning", "audio": {"path": str(wav_b)}},
    ]
    dataset = FakeDataset(samples)

    fake_settings = SimpleNamespace(AZURE_SPEECH_KEY="key", AZURE_SPEECH_REGION="region")
    monkeypatch.setattr("evals.transcription.src.evaluate.settings", fake_settings)
    monkeypatch.setattr("evals.transcription.src.evaluate.load_benchmark_dataset", lambda **_: dataset)
    monkeypatch.setattr("evals.transcription.src.evaluate.audio_duration_seconds", lambda _: 1.0)
    monkeypatch.setattr("evals.transcription.src.evaluate.WORKDIR", Path(tmp_path))

    monkeypatch.setattr(
        "evals.transcription.src.evaluate.AzureSTTAdapter",
        lambda **_: FakeAdapter("Azure Speech-to-Text", "hello world"),
    )
    monkeypatch.setattr(
        "evals.transcription.src.evaluate.WhisperAdapter",
        lambda **_: FakeAdapter("Whisper", "good morning"),
    )

    run_evaluation(num_samples=2)

    results_path = next((Path(tmp_path) / "results").glob("evaluation_results_*.json"))
    assert results_path.exists()
    results = json.loads(results_path.read_text(encoding="utf-8"))
    results = [
        {"summary": summary, "samples": results["engines"][summary["engine"]]} for summary in results["summaries"]
    ]
    assert len(results) == 2
    assert {r["summary"]["engine"] for r in results} == {"Azure Speech-to-Text", "Whisper"}

    for result in results:
        summary = result["summary"]
        assert summary["num_samples"] == 2
        assert summary["overall_wer_pct"] >= 0.0
        samples_out = result["samples"]
        assert [s["dataset_index"] for s in samples_out] == [0, 1]
        for sample in samples_out:
            assert sample["engine"] in {"Azure Speech-to-Text", "Whisper"}
            assert sample["audio_sec"] == 1.0
            assert sample["process_sec"] == 0.25
            assert sample["rtf"] == pytest.approx(0.25)
            assert sample["ref_raw"]
            assert sample["hyp_raw"]
            assert sample["ref_norm"]
            assert sample["hyp_norm"]
            assert isinstance(sample["diff_ops"], dict)
            assert {"equal", "replace", "delete", "insert"}.issubset(sample["diff_ops"])
            assert "engine_debug" in sample


def test_adapter_contracts(monkeypatch):
    async def fake_start(_path):
        return SimpleNamespace(transcript=[{"text": "hello"}, {"text": "world"}])

    monkeypatch.setattr("evals.transcription.src.adapters.azure.CommonAzureAdapter.start", fake_start)
    monkeypatch.setattr("evals.transcription.src.adapters.whisper.WhisplyLocalAdapter.start", fake_start)

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
