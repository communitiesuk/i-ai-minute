from jiwer import (
    process_words,
    Compose,
    ToLowerCase,
    RemovePunctuation,
    RemoveMultipleSpaces,
    Strip,
    ReduceToListOfListOfWords
)

transform = Compose([
    ToLowerCase(),
    RemovePunctuation(),
    RemoveMultipleSpaces(),
    Strip(),
    ReduceToListOfListOfWords()
])

def score_transcript(reference: str, hypothesis: str) -> dict[str, float|int]:
    pw = process_words(
        reference,
        hypothesis,
        reference_transform=transform,
        hypothesis_transform=transform,
    )

    return {
        "wer": pw.wer,
        "substitutions": pw.substitutions,
        "insertions": pw.insertions,
        "deletions": pw.deletions,
        "hits": pw.hits,
    }


