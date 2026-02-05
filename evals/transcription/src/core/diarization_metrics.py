from pyannote.core import Annotation, Segment
from pyannote.metrics.diarization import DiarizationErrorRate, JaccardErrorRate


def _segments_to_annotation(segments: list[dict], uri: str = "audio") -> Annotation:
    annotation = Annotation(uri=uri)
    for seg in segments:
        annotation[Segment(seg["start"], seg["end"])] = seg["speaker"]
    return annotation


def compute_der(
    ref_segments: list[dict],
    hyp_segments: list[dict],
    collar: float = 0.25,
) -> dict:
    if not ref_segments:
        return {
            "der": 100.0 if hyp_segments else 0.0,
            "miss": 0.0,
            "false_alarm": 100.0 if hyp_segments else 0.0,
            "confusion": 0.0,
        }

    ref_annotation = _segments_to_annotation(ref_segments)
    hyp_annotation = _segments_to_annotation(hyp_segments)

    metric = DiarizationErrorRate(collar=collar, skip_overlap=False)
    der_value = metric(ref_annotation, hyp_annotation)
    components = metric.compute_components(ref_annotation, hyp_annotation)

    total = components['total']
    if total > 0:
        miss_pct = (components['missed detection'] / total) * 100.0
        fa_pct = (components['false alarm'] / total) * 100.0
        confusion_pct = (components['confusion'] / total) * 100.0
    else:
        miss_pct = fa_pct = confusion_pct = 0.0

    return {
        "der": der_value * 100.0,
        "miss": miss_pct,
        "false_alarm": fa_pct,
        "confusion": confusion_pct,
    }


def compute_jer(ref_segments: list[dict], hyp_segments: list[dict]) -> dict:
    if not ref_segments or not hyp_segments:
        return {"jer": 100.0, "jaccard_index": 0.0}

    ref_annotation = _segments_to_annotation(ref_segments)
    hyp_annotation = _segments_to_annotation(hyp_segments)

    metric = JaccardErrorRate()
    jer_value = metric(ref_annotation, hyp_annotation)

    return {
        "jer": jer_value * 100.0,
        "jaccard_index": 1.0 - jer_value,
    }


def compute_speaker_count_error(ref_segments: list[dict], hyp_segments: list[dict]) -> dict:
    ref_speakers = set(seg["speaker"] for seg in ref_segments) if ref_segments else set()
    hyp_speakers = set(seg["speaker"] for seg in hyp_segments) if hyp_segments else set()

    ref_count = len(ref_speakers)
    hyp_count = len(hyp_speakers)
    absolute_error = abs(hyp_count - ref_count)

    return {
        "ref_speaker_count": ref_count,
        "hyp_speaker_count": hyp_count,
        "absolute_error": absolute_error,
    }


def compute_all_diarization_metrics(
    ref_segments: list[dict],
    hyp_segments: list[dict],
    collar: float = 0.25,
) -> dict:
    der_metrics = compute_der(ref_segments, hyp_segments, collar)
    jer_metrics = compute_jer(ref_segments, hyp_segments)
    speaker_count_metrics = compute_speaker_count_error(ref_segments, hyp_segments)

    return {
        "der": der_metrics,
        "jer": jer_metrics,
        "speaker_count": speaker_count_metrics,
        "component_breakdown": {
            "miss": der_metrics["miss"],
            "false_alarm": der_metrics["false_alarm"],
            "confusion": der_metrics["confusion"],
        },
    }
