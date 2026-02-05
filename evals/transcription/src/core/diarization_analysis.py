import numpy as np

from .diarization_metrics import compute_all_diarization_metrics


def compute_diarization_comparison(results: list) -> dict:
    if len(results) < 2:
        return {}

    ref_engine = results[0]["summary"]["engine"]
    ref_samples = results[0]["samples"]

    comparisons = {}

    for i in range(1, len(results)):
        hyp_engine = results[i]["summary"]["engine"]
        hyp_samples = results[i]["samples"]

        per_sample_metrics = []

        for ref_sample, hyp_sample in zip(ref_samples, hyp_samples):
            ref_diar = ref_sample.get("diarization", [])
            hyp_diar = hyp_sample.get("diarization", [])

            if not ref_diar or not hyp_diar:
                continue

            metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)
            per_sample_metrics.append(
                {
                    "dataset_index": ref_sample["dataset_index"],
                    "metrics": metrics,
                }
            )

        if not per_sample_metrics:
            summary_metrics = {}
        else:
            metric_extractors = {
                "der": lambda m: m["metrics"]["der"]["der"],
                "jer": lambda m: m["metrics"]["jer"]["jer"],
                "miss": lambda m: m["metrics"]["component_breakdown"]["miss"],
                "false_alarm": lambda m: m["metrics"]["component_breakdown"]["false_alarm"],
                "confusion": lambda m: m["metrics"]["component_breakdown"]["confusion"],
                "speaker_count_error": lambda m: m["metrics"]["speaker_count"]["absolute_error"],
            }

            summary_metrics = {
                name: {
                    "mean": float(np.mean(values := [extractor(m) for m in per_sample_metrics])),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }
                for name, extractor in metric_extractors.items()
            }

        comparisons[f"{ref_engine}_vs_{hyp_engine}"] = {
            "reference_engine": ref_engine,
            "hypothesis_engine": hyp_engine,
            "num_samples_compared": len(per_sample_metrics),
            "summary_metrics": summary_metrics,
            "per_sample_metrics": per_sample_metrics,
        }

    return comparisons


def compute_adapter_diarization_metrics(results: list) -> dict:
    adapter_diarization_metrics = {}
    
    for result in results:
        engine_name = result["summary"]["engine"]
        samples = result["samples"]

        per_sample_metrics = [
            {
                "der": (m := compute_all_diarization_metrics(
                    sample["reference_diarization"], sample["diarization"]
                ))["der"]["der"],
                "jer": m["jer"]["jer"],
                "miss": m["component_breakdown"]["miss"],
                "false_alarm": m["component_breakdown"]["false_alarm"],
                "confusion": m["component_breakdown"]["confusion"],
                "speaker_count_error": m["speaker_count"]["absolute_error"],
            }
            for sample in samples
            if sample.get("reference_diarization") and sample.get("diarization")
        ]

        if per_sample_metrics:
            adapter_diarization_metrics[engine_name] = {
                key: float(np.mean([m[key] for m in per_sample_metrics]))
                for key in ["der", "jer", "miss", "false_alarm", "confusion", "speaker_count_error"]
            }
        else:
            adapter_diarization_metrics[engine_name] = None

    return adapter_diarization_metrics
