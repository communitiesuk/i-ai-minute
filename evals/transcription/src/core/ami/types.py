from typing import TypedDict

MeetingId = str


class Utterance(TypedDict):
    audio: dict
    text: str
    begin_time: float
    end_time: float
    meeting_id: str


class Sample(TypedDict):
    audio: dict
    text: str
    meeting_id: str
    dataset_index: int
    duration_sec: float
    num_utterances: int
