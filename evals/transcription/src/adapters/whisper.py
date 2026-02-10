from common.services.transcription_services.whisply_local import WhisplyLocalAdapter

from evals.transcription.src.adapters.base import ServiceTranscriptionAdapter


def WhisperAdapter() -> ServiceTranscriptionAdapter:
    return ServiceTranscriptionAdapter(WhisplyLocalAdapter, "Whisply")
