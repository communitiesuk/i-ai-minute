import asyncio
import logging
import time
from pathlib import Path

from common.services.transcription_services.whisply_local import WhisplyLocalAdapter

from .base import TranscriptionAdapter

logger = logging.getLogger(__name__)


class WhisperAdapter(TranscriptionAdapter):
    def __init__(self, model_name: str = "large-v3-turbo", language: str = "en"):
        self.model_name = model_name
        self.language = language
        logger.info("Whisply adapter initialized with model: %s", model_name)

    def transcribe(self, wav_path: str):
        t0 = time.time()

        try:
            result = asyncio.run(WhisplyLocalAdapter.start(Path(wav_path)))
            t1 = time.time()

            dialogue_entries = result.transcript
            full_text = " ".join(entry["text"] for entry in dialogue_entries).strip()

            debug = {"model": self.model_name, "segments": len(dialogue_entries)}
            return full_text, (t1 - t0), debug

        except Exception as e:
            logger.error(f"Whisply transcription failed: {e}")
            t1 = time.time()
            return "", (t1 - t0), {"error": str(e)}
