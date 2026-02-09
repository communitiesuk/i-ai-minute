from __future__ import annotations

import pytest

from evals.transcription.src.core.runner import run_engines_parallel


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
