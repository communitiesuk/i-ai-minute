from .diarization import compute_wder
from .jaccard import compute_jaccard_wer
from .speaker_count import compute_speaker_count_metrics
from .transcription import compute_wer


def compute_all_metrics(
    ref_text: str,
    hyp_text: str,
    ref_segments: list[dict] | None = None,
    hyp_segments: list[dict] | None = None,
) -> dict:
    metrics = {}

    metrics["wer"] = compute_wer([ref_text], [hyp_text])
    metrics["jaccard_wer"] = compute_jaccard_wer([ref_text], [hyp_text])

    if ref_segments and hyp_segments:
        metrics["wder"] = compute_wder(ref_segments, hyp_segments)
        metrics["speaker_count"] = compute_speaker_count_metrics(ref_segments, hyp_segments)

    return metrics
