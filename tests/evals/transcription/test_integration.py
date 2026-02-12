from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import soundfile as sf

from evals.transcription.src.adapters.azure import AzureSTTAdapter
from evals.transcription.src.adapters.whisper import WhisperAdapter
from evals.transcription.src.evaluate import run_evaluation
from tests.evals.transcription.conftest import FakeAdapter, FakeDataset


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
    monkeypatch.setattr("evals.transcription.src.evaluate.get_duration", lambda _: 1.0)
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
            assert sample["processing_speed_ratio"] == pytest.approx(0.25)
            assert sample["ref_raw"]
            assert sample["hyp_raw"]
            assert sample["ref_norm"]
            assert sample["hyp_norm"]
            assert isinstance(sample["diff_ops"], dict)
            assert {"equal", "replace", "delete", "insert"}.issubset(sample["diff_ops"])
            assert "engine_debug" in sample


def test_adapter_contracts(tmp_path, monkeypatch):
    async def fake_start(_path):
        return SimpleNamespace(transcript=[{"text": "hello"}, {"text": "world"}])

    monkeypatch.setattr("evals.transcription.src.adapters.azure.CommonAzureAdapter.start", fake_start)
    monkeypatch.setattr("evals.transcription.src.adapters.whisper.WhisplyLocalAdapter.start", fake_start)

    wav_a = tmp_path / "a.wav"
    wav_b = tmp_path / "b.wav"
    sf.write(wav_a, [0.0, 0.0], 16000, subtype="PCM_16")
    sf.write(wav_b, [0.0, 0.0], 16000, subtype="PCM_16")

    azure = AzureSTTAdapter()
    result = azure.transcribe(str(wav_a))
    assert isinstance(result["text"], str)
    assert isinstance(result["duration_sec"], float)
    assert isinstance(result["debug_info"], dict)

    whisper = WhisperAdapter()
    result = whisper.transcribe(str(wav_b))
    assert isinstance(result["text"], str)
    assert isinstance(result["duration_sec"], float)
    assert isinstance(result["debug_info"], dict)


def test_run_evaluation_requires_azure_credentials(monkeypatch, tmp_path):
    wav_a = tmp_path / "a.wav"
    sf.write(wav_a, [0.0, 0.0], 16000, subtype="PCM_16")

    samples = [{"text": "hello world", "audio": {"path": str(wav_a)}}]
    dataset = FakeDataset(samples)
    fake_settings = SimpleNamespace(AZURE_SPEECH_KEY=None, AZURE_SPEECH_REGION=None)

    monkeypatch.setattr("common.services.transcription_services.azure.settings", fake_settings)
    monkeypatch.setattr("evals.transcription.src.evaluate.load_benchmark_dataset", lambda **_: dataset)
    monkeypatch.setattr("evals.transcription.src.evaluate.get_duration", lambda _: 1.0)
    monkeypatch.setattr("evals.transcription.src.evaluate.WORKDIR", Path(tmp_path))
    monkeypatch.setattr(
        "evals.transcription.src.evaluate.WhisperAdapter",
        lambda **_: FakeAdapter("Whisper", "hello world"),
    )

    run_evaluation(num_samples=1)

    results_path = next((Path(tmp_path) / "results").glob("evaluation_results_*.json"))
    results = json.loads(results_path.read_text(encoding="utf-8"))

    azure_samples = results["engines"]["Azure Speech API"]
    assert len(azure_samples) == 1
    assert "Azure credentials not found" in azure_samples[0]["engine_debug"]["error"]
