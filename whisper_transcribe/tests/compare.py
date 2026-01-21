from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, Strip, wer_default

# Normalization pipeline (case-insensitive, punctuation-insensitive)
_transform = Compose(
    [
    ToLowerCase(),
    RemovePunctuation(),
    Strip()
    ]
    +
    wer_default.transforms
)

def compare_transcripts(expected: str, predicted: str) -> dict:

    error = wer(
        expected,
        predicted,
        reference_transform=_transform,
        hypothesis_transform=_transform
    )

    """
    Returns:
        {
            "wer": float,
            "similarity": float (0–100),
        }
    """

    similarity = (1 - error) * 100

    return {
        "wer": error,
        "similarity": similarity
    }
