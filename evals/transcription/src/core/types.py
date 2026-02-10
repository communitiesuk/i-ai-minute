from __future__ import annotations

from typing import Callable, Protocol, TypedDict

import numpy
from numpy.typing import NDArray

from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter
from evals.transcription.src.core.metrics import TimingAccumulator

AudioArray = NDArray[numpy.floating]


class AdapterConfig(TypedDict):
    """
    Configuration for a transcription adapter.
    """

    adapter: EvalsTranscriptionAdapter


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
    """
    Protocol for dataset objects supporting indexing and length operations.
    """

    def __len__(self) -> int:
        pass

    def __getitem__(self, index: int) -> DatasetItem:
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


class Metrics(TypedDict):
    """
    Word Error Rate metrics including edit operation counts.
    """

    wer: float
    hits: int
    substitutions: int
    deletions: int
    insertions: int


class SampleRow(TypedDict):
    """
    Detailed transcription results for a single sample.
    """

    engine: str
    dataset_index: int
    wav_path: str
    audio_sec: float
    process_sec: float
    processing_speed_ratio: float | None
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
    processing_speed_ratio: float
    process_sec: float
    audio_sec: float
    per_sample_wer_min: float
    per_sample_wer_max: float
    per_sample_wer_mean: float


class EngineOutput(TypedDict):
    """
    Complete output from a transcription engine with summary and sample details.
    """

    summary: Summary
    samples: list[SampleRow]


WavWriteFn = Callable[[DatasetItem, int], str]
DurationFn = Callable[[str], float]
