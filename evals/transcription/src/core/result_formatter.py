import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _format_segments_with_speakers(segments: list[dict], speaker_map: dict = None) -> str:
    parts = []
    for seg in segments:
        text = seg.get("text", "")
        if not text:
            continue
        speaker = seg.get("speaker", "UNKNOWN")
        if speaker_map:
            speaker = speaker_map.get(speaker, speaker)
        parts.append(f"[{speaker}] {text}")
    return " ".join(parts)


def format_entry(sample: dict) -> dict:
    m = sample.get("metrics", {})
    ref_segments = sample.get("reference_diarization", [])
    hyp_segments = sample.get("diarization", [])
    
    ref_speaker_ids = sorted({seg.get("speaker") for seg in ref_segments if seg.get("text")})
    ref_speaker_map = {spk: f"Speaker_{i+1}" for i, spk in enumerate(ref_speaker_ids)}

    return {
        "dataset_index": sample["dataset_index"],
        "wer": m.get("wer", {}),
        "jaccard_wer": m.get("jaccard_wer", {}),
        "wder": m.get("wder", {}),
        "speaker_count": m.get("speaker_count", {}),
        "debug": {
            "ref_with_speakers": _format_segments_with_speakers(ref_segments, ref_speaker_map),
            "hyp_with_speakers": _format_segments_with_speakers(hyp_segments),
        }
    }


def _sum_metric(samples: list[dict], *keys) -> int:
    return sum(
        s.get("metrics", {}).get(keys[0], {}).get(keys[1], 0) 
        for s in samples
    )


def _format_metric_stats(agg: dict, key: str, precision: int = 4) -> dict:
    stats = agg[key]
    return {
        "mean": round(stats["mean"], precision),
        "min": round(stats["min"], precision),
        "max": round(stats["max"], precision),
        "std": round(stats["std"], precision),
    }


def format_adapter_result(result: dict) -> dict:
    summary = result["summary"]
    samples = result["samples"]
    agg = summary["aggregated_metrics"]

    total_misses = sum(
        1 for s in samples 
        if s.get("metrics", {}).get("speaker_count", {}).get("speaker_count_accuracy", 1.0) == 0.0
    )

    return {
        "engine": summary["engine"],
        "processing_time_ratio": round(summary["rtf"], 3),
        "word_metrics": {
            "hits": _sum_metric(samples, "wer", "hits"),
            "substitutions": _sum_metric(samples, "wer", "substitutions"),
            "deletions": _sum_metric(samples, "wer", "deletions"),
            "insertions": _sum_metric(samples, "wer", "insertions"),
            "speaker_confusions": _sum_metric(samples, "wder", "speaker_errors"),
            "total_words": _sum_metric(samples, "wder", "total_words"),
        },
        "wer": _format_metric_stats(agg, "wer_wer"),
        "jaccard_wer": _format_metric_stats(agg, "jaccard_wer_jaccard_wer"),
        "wder": _format_metric_stats(agg, "wder_wder"),
        "speaker_count_accuracy": {
            "accuracy": round(agg["speaker_count_speaker_count_accuracy"]["mean"] * 100, 1),
            "total_misses": total_misses,
        },
        "samples": [format_entry(s) for s in samples],
    }


def save_results(results: list, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    engines = [format_adapter_result(r) for r in results]
    combined = {"engines": engines}

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    logger.info("Results saved to %s", output_path)
