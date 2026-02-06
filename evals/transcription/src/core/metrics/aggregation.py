import numpy as np


def aggregate_metrics(all_sample_metrics: list[dict]) -> dict:
    aggregated = {}

    metric_keys = [
        "wer.wer",
        "jaccard_wer.jaccard_wer",
        "wder.wder",
        "speaker_count.speaker_count_accuracy",
    ]

    for key in metric_keys:
        parts = key.split(".")
        values = []

        for sample in all_sample_metrics:
            try:
                val = sample
                for part in parts:
                    val = val[part]
                if val is not None:
                    values.append(float(val))
            except (KeyError, TypeError):
                continue

        if values:
            aggregated[key.replace(".", "_")] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }

    return aggregated
