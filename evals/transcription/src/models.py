from __future__ import annotations

from typing import Callable, Protocol

import numpy
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

AudioArray = NDArray[numpy.floating]


class MeetingMetadata(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    meeting_ids: list[str]
    durations_sec: dict[str, float]


class RawAudioDict(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    array: NDArray[numpy.float32]
    sampling_rate: int


class AudioSample(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    array: AudioArray
    sampling_rate: int
    path: str


class DatasetItem(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio: AudioSample
    text: str


class RawDatasetRow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    meeting_id: str
    audio_id: str
    text: str
    audio: RawAudioDict
    begin_time: float
    end_time: float
    microphone_id: str
    speaker_id: str


class Utterance(BaseModel):
    audio: dict
    text: str
    begin_time: float
    end_time: float
    meeting_id: str


class AMIDatasetSample(DatasetItem):
    meeting_id: str
    dataset_index: int
    duration_sec: float
    num_utterances: int


class TranscriptionResult(BaseModel):
    text: str
    duration_sec: float
    debug_info: dict[str, object]


class DiffOps(BaseModel):
    equal: int
    replace: int
    delete: int
    insert: int


class Metrics(BaseModel):
    wer: float
    hits: int
    substitutions: int
    deletions: int
    insertions: int


class SampleRow(BaseModel):
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


class Summary(BaseModel):
    engine: str
    num_samples: int
    overall_wer_pct: float
    processing_speed_ratio: float
    process_sec: float
    audio_sec: float
    per_sample_wer_min: float
    per_sample_wer_max: float
    per_sample_wer_mean: float


class EngineOutput(BaseModel):
    summary: Summary
    samples: list[SampleRow]


class EngineResults(BaseModel):
    rows: list[SampleRow]
    timing: object


class MeetingSegment(BaseModel):
    meeting_id: str
    utterance_cutoff_time: float | None = None


class DatasetProtocol(Protocol):
    def __len__(self) -> int:
        pass

    def __getitem__(self, index: int) -> DatasetItem:
        pass


WavWriteFn = Callable[[DatasetItem, int], str]
DurationFn = Callable[[str], float]
