import asyncio
import logging
import time
from pathlib import Path

from common.services.transcription_services.azure import AzureSpeechAdapter as CommonAzureAdapter

from evals.transcription.src.adapters.base import TranscriptionAdapter

logger = logging.getLogger(__name__)


class AzureSTTAdapter(TranscriptionAdapter):
    def __init__(self, speech_key: str, speech_region: str, language: str = "en-GB"):
        if not speech_key or not speech_region:
            raise ValueError("Azure speech key and region are required")
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.language = language

    def transcribe(self, wav_path: str) -> tuple[str, float, dict[str, str]]:
        start_time = time.time()

        try:
            result = asyncio.run(CommonAzureAdapter.start(Path(wav_path)))
            end_time = time.time()

            dialogue_entries = result.transcript

            if not dialogue_entries:
                logger.error("Azure Speech API returned an empty transcript for %s", wav_path)
                return "", (end_time - start_time), {"error": "Empty transcript"}

            full_text = " ".join(entry["text"] for entry in dialogue_entries).strip()

            debug = {"segments": str(len(dialogue_entries))}
            return full_text, (end_time - start_time), debug

        except Exception as error:
            logger.error(f"Azure Speech API request failed: {error}")
            end_time = time.time()
            return "", (end_time - start_time), {"error": str(error)}
