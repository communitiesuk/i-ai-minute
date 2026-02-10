from pathlib import Path

from common.services.transcription_services.azure import AzureSpeechAdapter as CommonAzureAdapter
from common.types import TranscriptionJobMessageData

from evals.transcription.src.adapters.base import TranscriptionAdapter, TranscriptionResult


class AzureSTTAdapter(TranscriptionAdapter):
    _service_name = "Azure Speech API"

    def __init__(self, speech_key: str, speech_region: str, language: str = "en-GB"):
        if not speech_key or not speech_region:
            raise ValueError("Azure speech key and region are required")

    async def _run_transcription(self, wav_path: Path) -> TranscriptionJobMessageData:
        return await CommonAzureAdapter.start(wav_path)

    def _get_debug_info(self, dialogue_entries: list) -> dict[str, object]:
        return {"segments": str(len(dialogue_entries))}

    def transcribe(self, wav_path: str) -> "TranscriptionResult":
        return self._transcribe_with_service(wav_path)
