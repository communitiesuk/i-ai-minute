import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from whisply import models
from whisply.transcription import TranscriptionHandler

from common.database.postgres_models import DialogueEntry, Recording
from common.services.transcription_services.adapter import AdapterType, TranscriptionAdapter
from common.settings import get_settings
from common.types import TranscriptionJobMessageData

settings = get_settings()
logger = logging.getLogger(__name__)


class WhisplyLocalAdapter(TranscriptionAdapter):
    """Adapter for local Whisply transcription with speaker diarization."""

    max_audio_length = 14400
    name = "whisply_local"
    adapter_type = AdapterType.SYNCHRONOUS

    @classmethod
    async def start(cls, audio_file_path_or_recording: Path | Recording) -> TranscriptionJobMessageData:
        """
        Transcribe audio using local Whisply with speaker diarization
        """
        if isinstance(audio_file_path_or_recording, Recording):
            msg = "WhisplyLocalAdapter requires a local file path, not a Recording object"
            raise ValueError(msg)

        audio_file_path = audio_file_path_or_recording

        # Create temp directory for this transcription
        project_temp_dir = Path.cwd() / ".whisply_temp"
        project_temp_dir.mkdir(exist_ok=True)

        output_dir = project_temp_dir / f"output_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(exist_ok=True)

        logger.info(
            "Starting transcription: %s (model=%s, device=%s)",
            audio_file_path.name,
            settings.WHISPLY_MODEL,
            settings.WHISPLY_DEVICE,
        )

        try:
            if settings.WHISPLY_ENABLE_DIARIZATION and not settings.WHISPLY_HF_TOKEN:
                msg = "HuggingFace token required for speaker diarization. Set WHISPLY_HF_TOKEN."
                raise ValueError(msg)

            handler = TranscriptionHandler(
                base_dir=str(output_dir),
                model=settings.WHISPLY_MODEL,
                device=settings.WHISPLY_DEVICE,
                file_language=settings.WHISPLY_LANGUAGE,
                annotate=settings.WHISPLY_ENABLE_DIARIZATION,
                num_speakers=settings.WHISPLY_NUM_SPEAKERS,
                hf_token=settings.WHISPLY_HF_TOKEN if settings.WHISPLY_ENABLE_DIARIZATION else None,
                subtitle=False,
                translate=False,
                verbose=False,
                export_formats="json",
            )

            handler.sub_length = 5

            implementation = "whisperx" if settings.WHISPLY_ENABLE_DIARIZATION else "faster-whisper"
            handler.model = models.set_supported_model(
                model=handler.model_provided,
                implementation=implementation,
                translation=handler.translate,
            )

            if settings.WHISPLY_ENABLE_DIARIZATION:
                whisply_output = handler.transcribe_with_whisperx(audio_file_path)
            else:
                whisply_output = handler.transcribe_with_faster_whisper(audio_file_path)

            dialogue_entries = cls.convert_to_dialogue_entries(whisply_output)

            if not dialogue_entries:
                logger.error("No dialogue entries produced from transcription")
                msg = "Whisply transcription produced no dialogue entries"
                raise RuntimeError(msg)

            logger.info("Transcription complete: %d dialogue entries created", len(dialogue_entries))
            return TranscriptionJobMessageData(transcription_service=cls.name, transcript=dialogue_entries)

        except Exception as e:
            logger.error("Transcription failed: %s", e)
            raise

        finally:
            # Cleanup temp directory
            try:
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                    logger.debug("Cleaned up temp directory: %s", output_dir)
            except OSError as cleanup_error:
                logger.warning("Failed to cleanup temp directory %s: %s", output_dir, cleanup_error)

    @classmethod
    async def check(cls, data: TranscriptionJobMessageData) -> TranscriptionJobMessageData:
        return data

    @classmethod
    def is_available(cls) -> bool:
        try:
            import importlib.util

            return importlib.util.find_spec("whisply.transcription") is not None
        except ImportError:
            logger.warning("Whisply library is not available on this system")
            return False

    @classmethod
    def convert_to_dialogue_entries(cls, whisply_data: dict[str, Any]) -> list[DialogueEntry]:
        """
        Convert Whisply JSON output to DialogueEntry format.
        Whisply output structure: transcription -> transcriptions -> language -> chunks (with word-level speaker info)
        """
        dialogue_entries = []

        # Navigate to the transcription data
        transcription = whisply_data.get("transcription", {})
        transcriptions = transcription.get("transcriptions", {})

        if not transcriptions:
            logger.warning("No transcriptions data found in Whisply output")
            return dialogue_entries

        # Get first language (usually 'en')
        lang_key = next(iter(transcriptions.keys()), None)
        if not lang_key:
            logger.warning("No language key found in transcriptions")
            return dialogue_entries

        lang_data = transcriptions[lang_key]
        chunks = lang_data.get("chunks", [])

        # Group consecutive words by speaker to create dialogue entries
        current_speaker = None
        current_text = []
        current_start = None
        current_end = None

        for chunk in chunks:
            words = chunk.get("words", [])

            for word_data in words:
                speaker = word_data.get("speaker", "SPEAKER_00")
                word = word_data.get("word", "").strip()
                start = float(word_data.get("start", 0.0))
                end = float(word_data.get("end", 0.0))

                if not word:
                    continue

                # If speaker changes, save current entry and start new one
                if current_speaker and speaker != current_speaker:
                    if current_text:
                        dialogue_entries.append(
                            DialogueEntry(
                                speaker=current_speaker,
                                text=" ".join(current_text),
                                start_time=current_start,
                                end_time=current_end,
                            )
                        )
                    current_text = []
                    current_start = None

                # Add word to current entry
                if current_start is None:
                    current_start = start
                current_end = end
                current_speaker = speaker
                current_text.append(word)

        # Add final entry
        if current_text and current_speaker:
            dialogue_entries.append(
                DialogueEntry(
                    speaker=current_speaker,
                    text=" ".join(current_text),
                    start_time=current_start,
                    end_time=current_end,
                )
            )

        return dialogue_entries
