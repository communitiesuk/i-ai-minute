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
            assert sample["ref_raw"] in ["hello world", "good morning"]
            assert sample["ref_norm"] in ["hello world", "good morning"]

            if sample["engine"] == "Azure Speech-to-Text":
                expected_sample = {
                    "audio_sec": 1.0,
                    "process_sec": 0.25,
                    "hyp_raw": "hello world",
                    "hyp_norm": "hello world",
                    "engine_debug": {"label": "Azure Speech-to-Text"},
                }
            else:
                expected_sample = {
                    "audio_sec": 1.0,
                    "process_sec": 0.25,
                    "hyp_raw": "good morning",
                    "hyp_norm": "good morning",
                    "engine_debug": {"label": "Whisper"},
                }

            actual_sample = {k: sample[k] for k in expected_sample}
            assert expected_sample == actual_sample
            assert sample["processing_speed_ratio"] == pytest.approx(0.25)
            assert {"equal", "replace", "delete", "insert"}.issubset(sample["diff_ops"])


@pytest.mark.parametrize(
    ("adapter_class", "monkeypatch_target"),
    [
        (AzureSTTAdapter, "evals.transcription.src.adapters.azure.CommonAzureAdapter.start"),
        (WhisperAdapter, "evals.transcription.src.adapters.whisper.WhisplyLocalAdapter.start"),
    ],
)
def test_adapter_contracts(tmp_path, monkeypatch, adapter_class, monkeypatch_target):
    async def fake_start(_path):
        return SimpleNamespace(transcript=[{"text": "hello"}, {"text": "world"}])

    monkeypatch.setattr(monkeypatch_target, fake_start)

    wav_file = tmp_path / "test.wav"
    sf.write(wav_file, [0.0, 0.0], 16000, subtype="PCM_16")

    adapter = adapter_class()
    result = adapter.transcribe(str(wav_file))
    assert result.text == "hello world"
    assert result.duration_sec >= 0
    assert result.debug_info == {}


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
