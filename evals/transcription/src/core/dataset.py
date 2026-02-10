import logging
import tempfile
from pathlib import Path
from typing import cast

import soundfile
from common.audio.ffmpeg import convert_to_mp3

from evals.transcription.src.constants import (
    AUDIO_DIR,
    CACHE_DIR,
)
from evals.transcription.src.core.ami.audio import to_mono
from evals.transcription.src.core.ami.loader import AMIDatasetLoader
from evals.transcription.src.core.ami_dataset import load_ami_dataset
from evals.transcription.src.core.types import DatasetItem

logger = logging.getLogger(__name__)


def load_benchmark_dataset(
    num_samples: int | None, sample_duration_fraction: float | None = None
) -> AMIDatasetLoader:
    """
    Loads the AMI dataset with optional sampling of meetings and duration fractions.
    """
    logger.info("Loading AMI dataset with %d samples...", num_samples)
    logger.info("Using cache directory: %s", CACHE_DIR)

    ami_loader = load_ami_dataset(CACHE_DIR, num_samples, sample_duration_fraction)

    logger.info("Dataset loaded successfully")
    logger.info("Number of samples: %d", len(ami_loader))

    return ami_loader


def to_wav_16k_mono(example: DatasetItem, index: int) -> str:
    """
    Converts the input audio to mono MP3 format using ffmpeg (preserves sample rate).
    Caches the processed audio and returns the path to the processed file.
    """
    if "path" in example["audio"]:
        cached_path = example["audio"]["path"]
        if Path(cached_path).exists():
            return cast(str, cached_path)

    audio = example["audio"]
    audio_data = audio["array"]
    sample_rate = audio["sampling_rate"]

    output_path = AUDIO_DIR / f"sample_{index:06d}.mp3"

    audio_data = to_mono(audio_data)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        soundfile.write(temp_path, audio_data, sample_rate, subtype="PCM_16")

    try:
        convert_to_mp3(temp_path, output_path)
    finally:
        temp_path.unlink(missing_ok=True)

    return str(output_path)
