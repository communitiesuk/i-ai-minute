import jiwer

from typing import TypedDict, cast

class Ops(TypedDict):
    equal: int
    replace: int
    delete: int
    insert: int

class Metrics(TypedDict):
    wer: float
    mer: float
    wil: float
    cer: float
    hits: int
    substitutions: int
    deletions: int
    insertions: int



_jiwer_transform = jiwer.Compose(
    [
        jiwer.ToLowerCase(),
        jiwer.RemoveWhiteSpace(replace_by_space=True),
        jiwer.RemoveMultipleSpaces(),
        jiwer.RemovePunctuation(),
        jiwer.ReduceToListOfListOfWords(),
    ]
)


def normalise_text(s: str) -> str:
    if not s:
        return ""
    result = _jiwer_transform(s)
    if isinstance(result, list) and len(result) > 0:
        return " ".join(result[0]) if isinstance(result[0], list) else " ".join(result)
    return ""


def compute_wer_metrics(refs: list[str], hyps: list[str]) -> Metrics:

    if not refs or not hyps:
        return {
            "wer": 0.0,
            "mer": 0.0,
            "wil": 0.0,
            "cer": 0.0,
            "hits": 0,
            "substitutions": 0,
            "deletions": 0,
            "insertions": 0,
        }

    word_output = jiwer.process_words(
        refs,
        hyps,
        reference_transform=_jiwer_transform,
        hypothesis_transform=_jiwer_transform,
    )

    char_output = jiwer.process_characters(
        refs,
        hyps,
        reference_transform=_jiwer_transform,
        hypothesis_transform=_jiwer_transform,
    )

    return {
        "wer": float(word_output.wer),
        "mer": float(word_output.mer),
        "wil": float(word_output.wil),
        "cer": float(char_output.cer),
        "hits": int(word_output.hits),
        "substitutions": int(word_output.substitutions),
        "deletions": int(word_output.deletions),
        "insertions": int(word_output.insertions),
    }


def compute_wer_pct(refs: list[str], hyps: list[str], return_ops: bool = False) -> float | tuple[float, Ops]   :
    metrics = compute_wer_metrics(refs, hyps)
    wer_pct = metrics["wer"] * 100.0

    if return_ops:
        ops = cast(Ops, {
            "equal": metrics["hits"],
            "replace": metrics["substitutions"],
            "delete": metrics["deletions"],
            "insert": metrics["insertions"],
        })
        return wer_pct, ops

    return wer_pct


def token_ops(a: str, b: str) -> dict:
    metrics = compute_wer_metrics([a], [b])
    return {
        "equal": metrics["hits"],
        "replace": metrics["substitutions"],
        "delete": metrics["deletions"],
        "insert": metrics["insertions"],
    }


class TimingAccumulator:
    def __init__(self)-> None:
        self.process_sec = 0.0
        self.audio_sec = 0.0

    def add(self, audio_sec: float, process_sec: float)-> None:
        self.audio_sec += float(audio_sec)
        self.process_sec += float(process_sec)

    @property
    def rtf(self) -> float:
        return self.process_sec / self.audio_sec if self.audio_sec else float("nan")
