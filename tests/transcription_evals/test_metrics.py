from __future__ import annotations

from evals.transcription.src.core.metrics import compute_wer_metrics, compute_wer_pct, normalise_text


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
