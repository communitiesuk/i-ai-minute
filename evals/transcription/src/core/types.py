from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from evals.transcription.src.models import (
    AudioSample,
    DatasetItem,
    DatasetProtocol,
    DiffOps,
    DurationFn,
    EngineOutput,
    EngineResults,
    Metrics,
    SampleRow,
    Summary,
    WavWriteFn,
)

if TYPE_CHECKING:
    from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter


class AdapterConfig(TypedDict):
    adapter: EvalsTranscriptionAdapter


__all__ = [
    "AdapterConfig",
    "AudioSample",
    "DatasetItem",
    "DatasetProtocol",
    "DiffOps",
    "DurationFn",
    "EngineOutput",
    "EngineResults",
    "Metrics",
    "SampleRow",
    "Summary",
    "WavWriteFn",
]
