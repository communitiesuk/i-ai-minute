import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

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
    async def start(cls, audio_file_path_or_recording: Path | Recording) -> TranscriptionJobMessageData:  # noqa: C901, PLR0912, PLR0915
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

        import uuid

        output_dir = project_temp_dir / f"output_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(exist_ok=True)

        logger.info(
            "Starting transcription: %s (model=%s, device=%s)",
            audio_file_path.name,
            settings.WHISPLY_MODEL,
            settings.WHISPLY_DEVICE,
        )

        try:
            cmd = [
                "whisply",
                "run",
                "--files",
                str(audio_file_path),
                "--output_dir",
                str(output_dir),
                "--device",
                settings.WHISPLY_DEVICE,
                "--model",
                settings.WHISPLY_MODEL,
                "--lang",
                settings.WHISPLY_LANGUAGE,
                "--export",
                "json",
            ]

            if settings.WHISPLY_ENABLE_DIARIZATION:
                cmd.extend(["--annotate"])
                if settings.WHISPLY_NUM_SPEAKERS:
                    cmd.extend(["--num_speakers", str(settings.WHISPLY_NUM_SPEAKERS)])
                if settings.WHISPLY_HF_TOKEN:
                    cmd.extend(["--hf_token", settings.WHISPLY_HF_TOKEN])

            try:
                # Suppress Whisply's verbose logging by redirecting to devnull
                result = subprocess.run(  # noqa: S603, ASYNC221
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                    timeout=settings.WHISPLY_TIMEOUT,
                    env={**os.environ, "PYTHONWARNINGS": "ignore"},
                )
                if result.stderr and "error" in result.stderr.lower():
                    logger.warning("Whisply warnings: %s", result.stderr[:200])

            except subprocess.CalledProcessError as e:
                logger.error("Whisply failed with exit code %d: %s", e.returncode, e.stderr)
                msg = f"Whisply transcription failed: {e.stderr}"
                raise RuntimeError(msg) from e
            except subprocess.TimeoutExpired as e:
                logger.error("Whisply timed out after %d seconds", settings.WHISPLY_TIMEOUT)
                msg = f"Whisply transcription timed out after {settings.WHISPLY_TIMEOUT} seconds"
                raise RuntimeError(msg) from e

            # Find and parse JSON output
            json_files = list(output_dir.rglob("*.json"))

            if not json_files:
                logger.error("No JSON output found in %s", output_dir)
                msg = "No JSON output file found from Whisply"
                raise RuntimeError(msg)

            json_file = json_files[0]
            with json_file.open() as f:
                whisply_output = json.load(f)

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
            result = subprocess.run(  # noqa: S603
                ["whisply", "--help"],  # noqa: S607
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Whisply is not available on this system")
            return False

    @classmethod
    def convert_to_dialogue_entries(cls, whisply_data: dict[str, Any]) -> list[DialogueEntry]:
        """
        Convert Whisply JSON output to DialogueEntry format.
        Whisply output structure: transcription -> language -> chunks (with word-level speaker info)
        """
        dialogue_entries = []

        # Navigate to the transcription data
        transcription = whisply_data.get("transcription", {})

        # Get the language key (usually 'en')
        if not transcription:
            logger.warning("No transcription data found in Whisply output")
            return dialogue_entries

        # Get first language (usually 'en')
        lang_key = next(iter(transcription.keys()), None)
        if not lang_key:
            logger.warning("No language key found in transcription")
            return dialogue_entries

        lang_data = transcription[lang_key]
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
