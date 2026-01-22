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

        project_temp_dir = Path.cwd() / ".whisply_temp"
        project_temp_dir.mkdir(exist_ok=True)

        output_dir = project_temp_dir / f"output_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(exist_ok=True)

        try:
            if not settings.WHISPLY_HF_TOKEN:
                msg = "HuggingFace token required for speaker diarization. Set WHISPLY_HF_TOKEN."
                raise ValueError(msg)

            handler = TranscriptionHandler(
                base_dir=str(output_dir),
                model=settings.WHISPLY_MODEL,
                device=settings.WHISPLY_DEVICE,
                file_language="en",
                annotate=True,
                hf_token=settings.WHISPLY_HF_TOKEN,
                subtitle=False,
                translate=False,
                verbose=False,
                export_formats="json",
            )

            # Set internal processing chunk size (20s was used by OpenAI to train Whisper, the underlying model)
            handler.sub_length = 20

            handler.model = models.set_supported_model(
                model=handler.model_provided,
                implementation="whisperx",
                translation=handler.translate,
            )

            whisply_output = handler.transcribe_with_whisperx(audio_file_path)

            dialogue_entries = cls.convert_to_dialogue_entries(whisply_output)

            if not dialogue_entries:
                msg = "Whisply transcription produced no dialogue entries"
                raise RuntimeError(msg)

            return TranscriptionJobMessageData(transcription_service=cls.name, transcript=dialogue_entries)

        except Exception:
            raise

        finally:
            try:
                if output_dir.exists():
                    shutil.rmtree(output_dir)
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
            return False

    @classmethod
    def convert_to_dialogue_entries(cls, whisply_data: dict[str, Any]) -> list[DialogueEntry]:
        """
        Convert Whisply JSON output to DialogueEntry format.
        Whisply output structure: transcription -> transcriptions -> language -> chunks (with word-level speaker info)
        """
        dialogue_entries = []

        transcription = whisply_data.get("transcription", {})
        transcriptions = transcription.get("transcriptions", {})

        if not transcriptions:
            logger.warning("No transcriptions data found in Whisply output")
            return dialogue_entries

        lang_data = transcriptions["en"]
        chunks = lang_data.get("chunks", [])

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

                if current_start is None:
                    current_start = start
                current_end = end
                current_speaker = speaker
                current_text.append(word)

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
