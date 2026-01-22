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

        # Use a persistent directory for debugging
        project_temp_dir = Path.cwd() / ".whisply_temp"
        project_temp_dir.mkdir(exist_ok=True)
        
        # Create unique output directory that persists
        import uuid
        output_dir = project_temp_dir / f"output_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(exist_ok=True)
        
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

            # Find JSON output files
            json_files = list(output_dir.rglob("*.json"))
            logger.info(f"Found {len(json_files)} JSON files in {output_dir}")
            
            if not json_files:
                logger.error(f"No JSON output file found. Directory contents: {list(output_dir.rglob('*'))}")
                msg = "No JSON output file found from Whisply"
                raise RuntimeError(msg)

            json_file = json_files[0]
            logger.info(f"Reading JSON from: {json_file}")
            
            with open(json_file) as f:
                whisply_output = json.load(f)
            
            logger.info(f"Whisply output keys: {whisply_output.keys() if isinstance(whisply_output, dict) else 'not a dict'}")

            dialogue_entries = cls.convert_to_dialogue_entries(whisply_output)
            logger.info(f"Converted to {len(dialogue_entries)} dialogue entries")
            
            if not dialogue_entries:
                logger.error("Whisply produced no dialogue entries from output")
                logger.error(f"Whisply output sample: {str(whisply_output)[:500]}")
                msg = "Whisply transcription produced no dialogue entries"
                raise RuntimeError(msg)

            logger.info(f"Transcription successful. Output saved in: {output_dir}")
            return TranscriptionJobMessageData(transcription_service=cls.name, transcript=dialogue_entries)
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            logger.error(f"Output directory contents: {list(output_dir.rglob('*')) if output_dir.exists() else 'directory does not exist'}")
            raise

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
        
        logger.info(f"Processing {len(chunks)} chunks from Whisply output")
        
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
        
        logger.info(f"Created {len(dialogue_entries)} dialogue entries")
        return dialogue_entries
