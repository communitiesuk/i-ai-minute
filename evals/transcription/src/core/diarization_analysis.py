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
        aggregated_metrics = {
            "der": [],
            "jer": [],
            "miss": [],
            "false_alarm": [],
            "confusion": [],
            "speaker_count_error": [],
        }

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

            aggregated_metrics["der"].append(metrics["der"]["der"])
            aggregated_metrics["jer"].append(metrics["jer"]["jer"])
            aggregated_metrics["miss"].append(metrics["component_breakdown"]["miss"])
            aggregated_metrics["false_alarm"].append(metrics["component_breakdown"]["false_alarm"])
            aggregated_metrics["confusion"].append(metrics["component_breakdown"]["confusion"])
            aggregated_metrics["speaker_count_error"].append(
                metrics["speaker_count"]["absolute_error"]
            )

        summary_metrics = {}
        for metric_name, values in aggregated_metrics.items():
            if values:
                summary_metrics[metric_name] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
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

        per_sample_metrics = []
        for sample in samples:
            ref_diar = sample.get("reference_diarization", [])
            hyp_diar = sample.get("diarization", [])

            if ref_diar and hyp_diar:
                metrics = compute_all_diarization_metrics(ref_diar, hyp_diar)
                per_sample_metrics.append(
                    {
                        "der": metrics["der"]["der"],
                        "jer": metrics["jer"]["jer"],
                        "miss": metrics["component_breakdown"]["miss"],
                        "false_alarm": metrics["component_breakdown"]["false_alarm"],
                        "confusion": metrics["component_breakdown"]["confusion"],
                        "speaker_count_error": metrics["speaker_count"]["absolute_error"],
                    }
                )

        if per_sample_metrics:
            adapter_diarization_metrics[engine_name] = {
                "der": float(np.mean([m["der"] for m in per_sample_metrics])),
                "jer": float(np.mean([m["jer"] for m in per_sample_metrics])),
                "miss": float(np.mean([m["miss"] for m in per_sample_metrics])),
                "false_alarm": float(np.mean([m["false_alarm"] for m in per_sample_metrics])),
                "confusion": float(np.mean([m["confusion"] for m in per_sample_metrics])),
                "speaker_count_error": float(
                    np.mean([m["speaker_count_error"] for m in per_sample_metrics])
                ),
            }
        else:
            adapter_diarization_metrics[engine_name] = None

    return adapter_diarization_metrics
