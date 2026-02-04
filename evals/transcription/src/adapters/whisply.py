import logging
import shutil
import time
import uuid
from pathlib import Path

from .base import TranscriptionAdapter

logger = logging.getLogger(__name__)


class WhisplyAdapter(TranscriptionAdapter):
    def __init__(self, model: str = "large-v3", device: str = "cpu", hf_token: str | None = None):
        import torch

        self.model = model
        self.device = device
        self.hf_token = hf_token

        if not self.hf_token:
            msg = "HuggingFace token required for Whisply. Set hf_token parameter."
            raise ValueError(msg)

        try:
            from whisply import models
            from whisply.transcription import TranscriptionHandler

            self._whisply_models = models
            self._TranscriptionHandler = TranscriptionHandler
        except ImportError as e:
            msg = "Whisply not installed. Install with: pip install whisply"
            raise ImportError(msg) from e

        logger.info("Whisply adapter initialized with model '%s' on device: %s", model, device)
        logger.info(
            "MPS available: %s, MPS built: %s",
            torch.backends.mps.is_available(),
            torch.backends.mps.is_built(),
        )
        if device == "mps" and not torch.backends.mps.is_available():
            logger.warning("MPS device requested but not available, falling back to CPU")
            self.device = "cpu"

    def transcribe(self, wav_path: str):
        text, proc_sec, _ = self.transcribe_with_debug(wav_path)
        return text, proc_sec

    def transcribe_with_debug(self, wav_path: str):
        t0 = time.time()

        project_temp_dir = Path.cwd() / ".whisply_temp"
        project_temp_dir.mkdir(exist_ok=True)

        output_dir = project_temp_dir / f"output_{uuid.uuid4().hex[:8]}"
        output_dir.mkdir(exist_ok=True)

        try:
            handler = self._TranscriptionHandler(
                base_dir=str(output_dir),
                model=self.model,
                device=self.device,
                file_language="en",
                annotate=True,
                hf_token=self.hf_token,
                subtitle=False,
                translate=False,
                verbose=False,
                export_formats="json",
            )

            handler.sub_length = 20

            handler.model = self._whisply_models.set_supported_model(
                model=handler.model_provided,
                implementation="whisperx",
                translation=handler.translate,
            )

            handler.device = self.device

            logger.info(
                "Starting Whisply transcription with device: %s (handler.device: %s)",
                self.device,
                getattr(handler, "device", "unknown"),
            )

            whisply_output = handler.transcribe_with_whisperx(Path(wav_path))

            text, diarization = self._extract_text_and_diarization(whisply_output)

            t1 = time.time()

            import torch

            actual_device = "unknown"
            if torch.cuda.is_available() and self.device == "cuda":
                actual_device = "cuda (verified)"
            elif torch.backends.mps.is_available() and self.device == "mps":
                actual_device = "mps (verified)"
            else:
                actual_device = self.device

            logger.info(
                "Whisply transcription completed. Requested device: %s, Actual: %s",
                self.device,
                actual_device,
            )

            debug = {
                "model": self.model,
                "device": self.device,
                "actual_device": actual_device,
                "num_speakers": len(set(seg["speaker"] for seg in diarization))
                if diarization
                else 0,
                "num_segments": len(diarization) if diarization else 0,
                "diarization": diarization,
            }

            return text, (t1 - t0), debug

        except Exception as e:
            logger.error("Whisply transcription failed: %s", e)
            t1 = time.time()
            return "", (t1 - t0), {"error": str(e), "diarization": []}

        finally:
            try:
                if output_dir.exists():
                    shutil.rmtree(output_dir)
            except OSError as cleanup_error:
                logger.warning("Failed to cleanup temp directory %s: %s", output_dir, cleanup_error)

    def _extract_text_and_diarization(self, whisply_data: dict):
        transcription = whisply_data.get("transcription", {})
        transcriptions = transcription.get("transcriptions", {})
        lang_data = transcriptions.get("en", {})
        chunks = lang_data.get("chunks", [])

        current_speaker = None
        current_text = []
        current_start = None
        current_end = None
        diarization = []
        all_text = []

        for chunk in chunks:
            words = chunk.get("words", [])

            for word_data in words:
                speaker = word_data.get("speaker", "UNKNOWN")
                word = word_data.get("word", "").strip()
                start = word_data.get("start", 0.0)
                end = word_data.get("end", 0.0)

                if not word:
                    continue

                if current_speaker and speaker != current_speaker:
                    if current_text and current_start is not None and current_end is not None:
                        segment_text = " ".join(current_text)
                        diarization.append(
                            {
                                "speaker": current_speaker,
                                "text": segment_text,
                                "start": current_start,
                                "end": current_end,
                            }
                        )
                        all_text.append(segment_text)
                    current_text = []
                    current_start = None

                if current_start is None:
                    current_start = start
                current_end = end
                current_speaker = speaker
                current_text.append(word)

        if (
            current_text
            and current_speaker
            and current_start is not None
            and current_end is not None
        ):
            segment_text = " ".join(current_text)
            diarization.append(
                {
                    "speaker": current_speaker,
                    "text": segment_text,
                    "start": current_start,
                    "end": current_end,
                }
            )
            all_text.append(segment_text)

        full_text = " ".join(all_text)
        return full_text, diarization
