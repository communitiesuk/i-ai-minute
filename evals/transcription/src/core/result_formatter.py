import json
import logging
from pathlib import Path

from .diarization_analysis import (
    compute_adapter_diarization_metrics,
    compute_diarization_comparison,
)
from .diarization_metrics import compute_all_diarization_metrics

logger = logging.getLogger(__name__)


def format_entry(sample: dict, adapter_diarization_metrics: dict, engine_name: str) -> dict:
    ref_diar = sample.get("reference_diarization", [])
    hyp_diar = sample.get("diarization", [])
    entry_diarization_metrics = None

    if ref_diar and hyp_diar:
        metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)
        entry_diarization_metrics = {
            "der": metrics["der"]["der"],
            "jer": metrics["jer"]["jer"],
            "miss": metrics["component_breakdown"]["miss"],
            "false_alarm": metrics["component_breakdown"]["false_alarm"],
            "confusion": metrics["component_breakdown"]["confusion"],
            "speaker_count_error": metrics["speaker_count"]["absolute_error"],
        }

    results_section = {
        "wav_path": sample["wav_path"],
        "audio_sec": sample["audio_sec"],
        "process_sec": sample["process_sec"],
        "rtf": sample["rtf"],
        "wer_pct": sample["wer_pct"],
        "wer_metrics": sample.get("wer_metrics", {}),
        "diff_ops": sample["diff_ops"],
    }

    if entry_diarization_metrics:
        results_section["diarization"] = entry_diarization_metrics

    entry = {
        "dataset_index": sample["dataset_index"],
        "results": results_section,
        "debug": {
            "ref_raw": sample["ref_raw"],
            "hyp_raw": sample["hyp_raw"],
            "diarization": sample.get("diarization", []),
            "engine_debug": sample.get("engine_debug", {}),
        },
    }
    return entry


def format_adapter_result(result: dict, adapter_diarization_metrics: dict) -> dict:
    summary = result["summary"]
    samples = result["samples"]
    engine_name = summary["engine"]

    entries = [format_entry(sample, adapter_diarization_metrics, engine_name) for sample in samples]

    wer_metrics = summary.get("overall_wer_metrics", {})
    wer_metrics_pct = {
        "wer": wer_metrics.get("wer", 0.0) * 100.0,
        "mer": wer_metrics.get("mer", 0.0) * 100.0,
        "wil": wer_metrics.get("wil", 0.0) * 100.0,
        "cer": wer_metrics.get("cer", 0.0) * 100.0,
        "hits": wer_metrics.get("hits", 0),
        "substitutions": wer_metrics.get("substitutions", 0),
        "deletions": wer_metrics.get("deletions", 0),
        "insertions": wer_metrics.get("insertions", 0),
    }

    overall_results = {
        "num_samples": summary["num_samples"],
        "overall_wer_pct": summary["overall_wer_pct"],
        "overall_wer_metrics": wer_metrics_pct,
        "per_sample_wer_min": summary["per_sample_wer_min"],
        "per_sample_wer_max": summary["per_sample_wer_max"],
        "per_sample_wer_mean": summary["per_sample_wer_mean"],
        "per_sample_wer_std": summary.get("per_sample_wer_std"),
        "rtf": summary["rtf"],
        "process_sec": summary["process_sec"],
        "audio_sec": summary["audio_sec"],
    }

    if (
        engine_name in adapter_diarization_metrics
        and adapter_diarization_metrics[engine_name] is not None
    ):
        overall_results["diarization"] = adapter_diarization_metrics[engine_name]

    return {
        "name": engine_name,
        "overall_results": overall_results,
        "entries": entries,
    }


def log_diarization_comparison(diarization_comparison: dict):
    if not diarization_comparison:
        return

    logger.info("\n=== Diarization Comparison Metrics ===")
    for comparison_name, comparison_data in diarization_comparison.items():
        logger.info("\n%s:", comparison_name)
        summary = comparison_data["summary_metrics"]
        if "der" in summary:
            logger.info("  DER: %.2f%% (±%.2f)", summary["der"]["mean"], summary["der"]["std"])
            logger.info(
                "    - Miss: %.2f%% (±%.2f)", summary["miss"]["mean"], summary["miss"]["std"]
            )
            logger.info(
                "    - False Alarm: %.2f%% (±%.2f)",
                summary["false_alarm"]["mean"],
                summary["false_alarm"]["std"],
            )
            logger.info(
                "    - Confusion: %.2f%% (±%.2f)",
                summary["confusion"]["mean"],
                summary["confusion"]["std"],
            )
        if "jer" in summary:
            logger.info("  JER: %.2f%% (±%.2f)", summary["jer"]["mean"], summary["jer"]["std"])
        if "speaker_count_error" in summary:
            logger.info(
                "  Speaker Count Error: %.2f (±%.2f)",
                summary["speaker_count_error"]["mean"],
                summary["speaker_count_error"]["std"],
            )


def save_results(results: list, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    diarization_comparison = compute_diarization_comparison(results)
    adapter_diarization_metrics = compute_adapter_diarization_metrics(results)

    adapters = [format_adapter_result(r, adapter_diarization_metrics) for r in results]

    combined = {"adapters": adapters}

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_path)
    log_diarization_comparison(diarization_comparison)
