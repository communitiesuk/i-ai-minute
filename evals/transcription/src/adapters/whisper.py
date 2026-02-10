from pathlib import Path

from common.services.transcription_services.whisply_local import WhisplyLocalAdapter
from common.types import TranscriptionJobMessageData

from evals.transcription.src.adapters.base import TranscriptionAdapter, TranscriptionResult


class WhisperAdapter(TranscriptionAdapter):
    _service_name = "Whisply"

    async def _run_transcription(self, wav_path: Path) -> TranscriptionJobMessageData:
        return await WhisplyLocalAdapter.start(wav_path)

    def _get_debug_info(self, dialogue_entries: list) -> dict[str, object]:
        return {"segments": len(dialogue_entries)}

    def transcribe(self, wav_path: str) -> TranscriptionResult:
        return self._transcribe_with_service(wav_path)
