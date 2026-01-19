import json
import logging
import subprocess
import tempfile
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
    async def start(cls, audio_file_path_or_recording: Path | Recording) -> TranscriptionJobMessageData:
        """
        Transcribe audio using local Whisply with speaker diarization
        """
        if isinstance(audio_file_path_or_recording, Recording):
            msg = "WhisplyLocalAdapter requires a local file path, not a Recording object"
            raise ValueError(msg)

        audio_file_path = audio_file_path_or_recording

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

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

            logger.info("Running Whisply transcription: %s", " ".join(cmd))

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=settings.WHISPLY_TIMEOUT,
                )
                logger.info("Whisply output: %s", result.stdout)
                if result.stderr:
                    logger.warning("Whisply stderr: %s", result.stderr)

            except subprocess.CalledProcessError as e:
                logger.error("Whisply failed with exit code %d: %s", e.returncode, e.stderr)
                msg = f"Whisply transcription failed: {e.stderr}"
                raise RuntimeError(msg) from e
            except subprocess.TimeoutExpired as e:
                logger.error("Whisply timed out after %d seconds", settings.WHISPLY_TIMEOUT)
                msg = f"Whisply transcription timed out after {settings.WHISPLY_TIMEOUT} seconds"
                raise RuntimeError(msg) from e

            json_files = list(output_dir.glob("*.json"))
            if not json_files:
                msg = "No JSON output file found from Whisply"
                raise RuntimeError(msg)

            json_file = json_files[0]
            with open(json_file) as f:
                whisply_output = json.load(f)

            dialogue_entries = cls.convert_to_dialogue_entries(whisply_output)
            
            if not dialogue_entries:
                logger.error("Whisply produced no dialogue entries from output")
                msg = "Whisply transcription produced no dialogue entries"
                raise RuntimeError(msg)

            return TranscriptionJobMessageData(transcription_service=cls.name, transcript=dialogue_entries)

    @classmethod
    async def check(cls, data: TranscriptionJobMessageData) -> TranscriptionJobMessageData:
        return data

    @classmethod
    def is_available(cls) -> bool:
        try:
            result = subprocess.run(
                ["whisply", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Whisply is not available on this system")
            return False

    @classmethod
    def convert_to_dialogue_entries(cls, whisply_data: dict[str, Any]) -> list[DialogueEntry]:
        """
        Convert Whisply JSON output to DialogueEntry format.
        Whisply output structure varies based on whether diarization is enabled.
        """
        dialogue_entries = []

        segments = whisply_data.get("segments", [])

        for segment in segments:
            speaker = segment.get("speaker", "SPEAKER_00")
            text = segment.get("text", "").strip()
            start_time = float(segment.get("start", 0.0))
            end_time = float(segment.get("end", 0.0))

            if text:
                dialogue_entries.append(
                    DialogueEntry(
                        speaker=speaker,
                        text=text,
                        start_time=start_time,
                        end_time=end_time,
                    )
                )

        return dialogue_entries
