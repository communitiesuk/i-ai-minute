import logging
import tempfile
from pathlib import Path
from typing import cast

import ffmpeg  # type: ignore[import-untyped]
import numpy as np
import soundfile as sf

from evals.transcription.src.constants import TARGET_SAMPLE_RATE
from evals.transcription.src.core.ami.selection import MeetingSegment

logger = logging.getLogger(__name__)


class CachePaths:
    def __init__(self, wav_path: Path, transcript_path: Path):
        self.wav = wav_path
        self.transcript = transcript_path

    def is_complete(self) -> bool:
        return self.wav.exists() and self.transcript.exists()


def get_cache_paths(processed_dir: Path, segment: MeetingSegment, idx: int) -> CachePaths:
    """
    Using the given path, meeting segment, and index, returns the expected cache paths for the wav file and transcript.
    """
    wav_path = processed_dir / f"{segment.meeting_id}_{idx:06d}.wav"
    transcript_path = wav_path.with_suffix(".txt")
    return CachePaths(wav_path, transcript_path)


def load_audio(path: Path) -> np.ndarray:
    """
    Loads the audio from the given path and returns it as a numpy array.
    """
    audio, sr = sf.read(path)
    if sr != TARGET_SAMPLE_RATE:
        logger.warning(
            "Cached audio has unexpected sample rate %d, expected %d",
            sr,
            TARGET_SAMPLE_RATE,
        )
    return cast(np.ndarray, audio)


def save_audio(path: Path, audio: np.ndarray, sr: int = TARGET_SAMPLE_RATE) -> None:
    """
    Saves the given audio array to the specified path with the target sample rate.
    If the original sample rate is different from the target, it resamples the audio before saving
    """
    if sr == TARGET_SAMPLE_RATE:
        sf.write(path, audio, sr, subtype="PCM_16")
    else:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            sf.write(temp_path, audio, sr, subtype="PCM_16")

        try:
            input_stream = ffmpeg.input(str(temp_path))
            output_stream = ffmpeg.output(
                input_stream,
                str(path),
                acodec="pcm_s16le",
                ar=TARGET_SAMPLE_RATE,
                ac=1,
                loglevel="error",
            )
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
        finally:
            temp_path.unlink(missing_ok=True)


def load_transcript(path: Path) -> str:
    """
    Loads the transcript text from the given path and returns it as a string.
    """
    return path.read_text(encoding="utf-8")


def save_transcript(path: Path, text: str) -> None:
    """
    Saves the given transcript text to the specified path.
    """
    path.write_text(text, encoding="utf-8")
