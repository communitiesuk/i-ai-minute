from __future__ import annotations

from typing import TypedDict

import numpy as np
from numpy.typing import NDArray

from evals.transcription.src.core.types import DatasetItem

MeetingId = str


class RawAudioDict(TypedDict):
    """Audio representation from HuggingFace datasets"""

    array: NDArray[np.float32]
    sampling_rate: int


class RawDatasetRow(TypedDict):
    """Raw utterance row from the AMI dataset as returned by HuggingFace datasets."""

    meeting_id: str
    audio_id: str
    text: str
    audio: RawAudioDict
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
