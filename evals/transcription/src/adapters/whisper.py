import asyncio
import logging
import time
from pathlib import Path

from common.services.transcription_services.whisply_local import WhisplyLocalAdapter

from evals.transcription.src.adapters.base import TranscriptionAdapter

logger = logging.getLogger(__name__)


class WhisperAdapter(TranscriptionAdapter):
    def __init__(self, model_name: str = "large-v3-turbo", language: str = "en"):
        self.model_name = model_name
        self.language = language
        logger.info("Whisply adapter initialized with model: %s", model_name)

    def transcribe(self, wav_path: str) -> tuple[str, float, dict[str, object]]:
        start_time = time.time()

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(WhisplyLocalAdapter.start(Path(wav_path)))
            end_time = time.time()

            dialogue_entries = result.transcript

            if not dialogue_entries:
                logger.error("Whisply returned an empty transcript for %s", wav_path)
                return "", (end_time - start_time), {"error": "Empty transcript"}

            full_text = " ".join(entry["text"] for entry in dialogue_entries).strip()

            debug = {"model": self.model_name, "segments": len(dialogue_entries)}
            return full_text, (end_time - start_time), debug

        except Exception as error:
            logger.error(f"Whisply transcription failed: {error}")
            end_time = time.time()
            return "", (end_time - start_time), {"error": str(error)}
