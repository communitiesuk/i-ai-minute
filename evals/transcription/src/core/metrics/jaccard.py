from .transforms import jiwer_transform


def compute_jaccard_wer(refs: list[str], hyps: list[str]) -> dict:
    if not refs or not hyps:
        return {"jaccard_wer": 0.0}

    ref_words_set = set()
    hyp_words_set = set()

    for ref in refs:
        words = jiwer_transform([ref])
        if words and isinstance(words[0], list):
            ref_words_set.update(words[0])

    for hyp in hyps:
        words = jiwer_transform([hyp])
        if words and isinstance(words[0], list):
            hyp_words_set.update(words[0])

    intersection = len(ref_words_set & hyp_words_set)
    union = len(ref_words_set | hyp_words_set)

    jaccard_similarity = intersection / union if union > 0 else 0.0
    jaccard_wer = 1.0 - jaccard_similarity

    return {
        "jaccard_wer": float(jaccard_wer),
    }
