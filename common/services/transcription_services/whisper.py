import logging
from pathlib import Path

import httpx
from common.services.transcription_services.adapter import AdapterType, TranscriptionAdapter
from common.settings import get_settings
from common.types import TranscriptionJobMessageData

logger = logging.getLogger(__name__)
settings = get_settings()


class WhisperAdapter(TranscriptionAdapter):
    max_audio_length = 60 * 60 * 4  # 4 hours
    name = "whisper"
    adapter_type = AdapterType.SYNCHRONOUS

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    async def start(
        cls, audio_file_path_or_recording: Path | object
    ) -> TranscriptionJobMessageData:
        if isinstance(audio_file_path_or_recording, Path):
            path = audio_file_path_or_recording
        else:
            # If it's a Recording object, we expect that the calling code (manager)
            # has already downloaded it to a temp file and passed that path.
            # However, the manager logic for SYNCHRONOUS adapters currently calls start(file_path).
            # So this branch might not be hit if the manager logic is correct.
            # But adapting to the signature:
            msg = "LLM returned schema definition instead of actual values"
            raise ValueError(msg)

        logger.info("Starting transcription for file: %s", path)
        
        async with httpx.AsyncClient(timeout=3600) as client: # LONG timeout for transcription
            with open(path, "rb") as f:
                files = {"file": f}
                # faster-whisper-server provides an OpenAI compatible endpoint
                # /v1/audio/transcriptions
                url = f"{settings.WHISPER_URL}/audio/transcriptions"
                data = {
                    "model": "whisper-1", # Ignored by faster-whisper-server usually, but required by API
                    "response_format": "verbose_json"
                }
                
                try:
                    response = await client.post(url, files=files, data=data)
                    response.raise_for_status()
                except httpx.RequestError as exc:
                    logger.error("An error occurred while requesting %r.",  exc.request.url)
                    raise
                except httpx.HTTPStatusError as exc:
                    logger.error("Error response %s while requesting %r.", exc.response.status_code, exc.request.url)
                    raise

                result = response.json()
                
                # Convert OpenAI verbose_json format to our internal format
                # OpenAI format: {"task": "transcribe", "language": "english", "duration": 12.3, "text": "...", "segments": [...]}
                # Our format (TranscriptionJobMessageData.transcript): list[DialogueEntry]
                # DialogueEntry = TypedDict("DialogueEntry", {"start": float, "end": float, "text": str, "speaker": int})
                
                transcript_entries: list[DialogueEntry] = []
                for segment in result.get("segments", []):
                    transcript_entries.append({
                        "start": segment.get("start"),
                        "end": segment.get("end"),
                        "text": segment.get("text").strip(),
                        "speaker": 0 # TODO: Diarization support if faster-whisper-server provides it
                    })

                return TranscriptionJobMessageData(
                    job_name=path.name,
                    transcription_service=cls.name,
                    transcript=cast(list[DialogueEntry], transcript_entries)
                    # We can store raw response or other metadata if needed, but for now just the transcript
                )


    @classmethod
    async def check(cls, data: TranscriptionJobMessageData) -> TranscriptionJobMessageData:
        return data
