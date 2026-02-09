from typing import TypedDict

from evals.transcription.src.core.types import DatasetItem

MeetingId = str


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
