from __future__ import annotations

from typing import Callable, Protocol, TypedDict

import numpy as np
from numpy.typing import NDArray

from evals.transcription.src.core.metrics import TimingAccumulator


AudioArray = NDArray[np.floating]


class AdapterProtocol(Protocol):
    def transcribe(self, wav_path: str) -> tuple[str, float, dict[str, object]]:
        pass


class AdapterConfig(TypedDict):
    adapter: AdapterProtocol
    label: str


class AudioSample(TypedDict):
    array: AudioArray
    sampling_rate: int
    path: str


class DatasetItem(TypedDict):
    audio: AudioSample
    text: str


class DatasetProtocol(Protocol):
    def __len__(self) -> int:
        pass

    def __getitem__(self, idx: int) -> DatasetItem:
        pass


class EngineResults(TypedDict):
    rows: list["SampleRow"]
    timing: TimingAccumulator


class DiffOps(TypedDict):
    equal: int
    replace: int
    delete: int
    insert: int


class SampleRow(TypedDict):
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
    summary: Summary
    samples: list[SampleRow]


WavWriteFn = Callable[[DatasetItem, int], str]
DurationFn = Callable[[str], float]
