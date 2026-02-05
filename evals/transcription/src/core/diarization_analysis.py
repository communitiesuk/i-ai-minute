import numpy as np

from .diarization_metrics import compute_all_diarization_metrics


def compute_adapter_diarization_metrics(results: list) -> dict:
    adapter_diarization_metrics = {}

    for result in results:
        engine_name = result["summary"]["engine"]
        samples = result["samples"]

        per_sample_metrics = [
            {
                "der": (
                    m := compute_all_diarization_metrics(
                        sample["reference_diarization"], sample["diarization"]
                    )
                )["der"]["der"],
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
