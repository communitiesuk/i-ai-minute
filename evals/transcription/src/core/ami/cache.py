import logging
from pathlib import Path

import numpy as np
import soundfile as sf

from .constants import TARGET_SAMPLE_RATE
from .selection import MeetingSegment

logger = logging.getLogger(__name__)


class CachePaths:
    def __init__(self, wav_path: Path, transcript_path: Path):
        self.wav = wav_path
        self.transcript = transcript_path

    def is_complete(self) -> bool:
        return self.wav.exists() and self.transcript.exists()


def get_cache_paths(processed_dir: Path, segment: MeetingSegment, idx: int) -> CachePaths:
    wav_path = processed_dir / f"{segment.meeting_id}_{idx:06d}.wav"
    transcript_path = wav_path.with_suffix(".txt")
    return CachePaths(wav_path, transcript_path)


def load_audio(path: Path) -> np.ndarray:
    audio, sr = sf.read(path)
    if sr != TARGET_SAMPLE_RATE:
        logger.warning("Cached audio has unexpected sample rate %d, expected %d", sr, TARGET_SAMPLE_RATE)
    return audio


def save_audio(path: Path, audio: np.ndarray, sr: int = TARGET_SAMPLE_RATE) -> None:
    sf.write(path, audio, sr, subtype="PCM_16")


def load_transcript(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def save_transcript(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
