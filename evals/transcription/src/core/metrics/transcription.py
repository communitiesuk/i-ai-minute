import jiwer

from .transforms import jiwer_transform


def compute_wer(refs: list[str], hyps: list[str]) -> dict:
    if not refs or not hyps:
        return {
            "wer": 0.0,
            "hits": 0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": 0,
        }

    word_output = jiwer.process_words(
        refs,
        hyps,
        reference_transform=jiwer_transform,
        hypothesis_transform=jiwer_transform,
    )

    return {
        "wer": float(word_output.wer),
        "hits": int(word_output.hits),
        "substitutions": int(word_output.substitutions),
        "deletions": int(word_output.deletions),
        "insertions": int(word_output.insertions),
    }
