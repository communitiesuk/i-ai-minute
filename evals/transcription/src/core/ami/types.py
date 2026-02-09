from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable

import numpy as np

from evals.transcription.src.core.types import DatasetItem

MeetingId = str


@runtime_checkable
class RawAudioSample(Protocol):
    """
    Audio object returned by HuggingFace datasets library.

    Note: This protocol only defines properties actually used in the codebase.
    The underlying audio decoder has additional methods not listed here.
    """

    array: np.ndarray
    sampling_rate: int


class RawDatasetRow(TypedDict):
    """Raw utterance row from the AMI dataset as returned by HuggingFace datasets."""

    meeting_id: str
    audio_id: str
    text: str
    audio: RawAudioSample
    begin_time: float
    end_time: float
    microphone_id: str
    speaker_id: str


class Utterance(TypedDict):
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
