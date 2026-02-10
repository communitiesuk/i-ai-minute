from __future__ import annotations

from typing import Callable, Protocol, TypedDict

import numpy as np
from numpy.typing import NDArray

from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter
from evals.transcription.src.core.metrics import TimingAccumulator

AudioArray = NDArray[np.floating]


class AdapterConfig(TypedDict):
    """
    Configuration for a transcription adapter with its label.
    """

    adapter: EvalsTranscriptionAdapter
    label: str


class AudioSample(TypedDict):
    """
    Audio data with array, sample rate, and file path.
    """

    array: AudioArray
    sampling_rate: int
    path: str


class DatasetItem(TypedDict):
    """
    Single dataset sample with audio and reference text.
    """

    audio: AudioSample
    text: str


class DatasetProtocol(Protocol):
    def __len__(self) -> int:
        pass

    def __getitem__(self, idx: int) -> DatasetItem:
        pass


class EngineResults(TypedDict):
    """
    Results from a transcription engine including sample rows and timing data.
    """

    rows: list["SampleRow"]
    timing: TimingAccumulator


class DiffOps(TypedDict):
    """
    Word-level edit operations from WER calculation.
    """

    equal: int
    replace: int
    delete: int
    insert: int


class SampleRow(TypedDict):
    """
    Detailed transcription results for a single sample.
    """

    engine: str
    dataset_index: int
    wav_path: str
    audio_sec: float
    process_sec: float
    rtf: float | None
    wer_pct: float
    diff_ops: DiffOps
    ref_raw: str
    hyp_raw: str
    ref_norm: str
    hyp_norm: str
    engine_debug: dict[str, object]


class Summary(TypedDict):
    """
    Aggregate metrics for a transcription engine across all samples.
    """

    engine: str
    num_samples: int
    overall_wer_pct: float
    rtf: float
    process_sec: float
    audio_sec: float
    per_sample_wer_min: float | None
    per_sample_wer_max: float | None
    per_sample_wer_mean: float | None


class EngineOutput(TypedDict):
    """
    Complete output from a transcription engine with summary and sample details.
    """

    summary: Summary
    samples: list[SampleRow]


WavWriteFn = Callable[[DatasetItem, int], str]
DurationFn = Callable[[str], float]
