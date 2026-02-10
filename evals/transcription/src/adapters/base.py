import asyncio
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypedDict

from common.types import TranscriptionJobMessageData

logger = logging.getLogger(__name__)


class TranscriptionResult(TypedDict):
    """Result from a transcription operation."""

    text: str
    duration_sec: float
    debug_info: dict[str, object]


class TranscriptionAdapter(ABC):
    _service_name: str

    @abstractmethod
    def transcribe(self, wav_path: str) -> TranscriptionResult:
        """Transcribe the given wav file."""
        pass

    @abstractmethod
    async def _run_transcription(self, wav_path: Path) -> TranscriptionJobMessageData:
        """Run the actual transcription service."""
        pass

    def _transcribe_with_service(self, wav_path: str) -> TranscriptionResult:
        """Shared transcription logic for all adapters."""
        start_time = time.time()

        try:
            result = asyncio.run(self._run_transcription(Path(wav_path)))
            end_time = time.time()

            dialogue_entries = result.transcript

            if not dialogue_entries:
                logger.error("%s returned an empty transcript for %s", self._service_name, wav_path)
                return {
                    "text": "",
                    "duration_sec": (end_time - start_time),
                    "debug_info": {"error": "Empty transcript"},
                }

            full_text = " ".join(entry["text"] for entry in dialogue_entries).strip()

            return {"text": full_text, "duration_sec": (end_time - start_time), "debug_info": {}}

        except Exception as error:
            logger.error("%s transcription failed: %s", self._service_name, error)
            end_time = time.time()
            return {
                "text": "",
                "duration_sec": (end_time - start_time),
                "debug_info": {"error": str(error)},
            }
