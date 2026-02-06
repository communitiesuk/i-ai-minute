import logging
import tempfile
from pathlib import Path
from typing import Any

import ffmpeg
import soundfile as sf

from .ami_dataset import audio_duration_seconds as ami_audio_duration
from .ami_dataset import load_ami_dataset

logger = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 16000
STEREO_CHANNELS = 2

WORKDIR = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = WORKDIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
AUDIO_DIR = WORKDIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)


def load_benchmark_dataset(num_samples: int | None, sample_duration_fraction: float | None = None):
    logger.info("Loading AMI dataset with %d samples...", num_samples)
    logger.info("Using cache directory: %s", CACHE_DIR)

    ami_loader = load_ami_dataset(CACHE_DIR, num_samples, sample_duration_fraction)

    logger.info("Dataset loaded successfully")
    logger.info("Number of samples: %d", len(ami_loader))

    return ami_loader


def to_wav_16k_mono(example: dict[str, Any], idx: int) -> str:
    if "path" in example["audio"]:
        cached_path = example["audio"]["path"]
        if Path(cached_path).exists():
            return cached_path

    audio = example["audio"]
    y = audio["array"]
    sr = audio["sampling_rate"]

    output_path = AUDIO_DIR / f"sample_{idx:06d}.wav"

    if getattr(y, "ndim", 1) == STEREO_CHANNELS:
        y = y.mean(axis=1)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        sf.write(temp_path, y, sr, subtype="PCM_16")

    try:
        input_stream = ffmpeg.input(str(temp_path))
        output_stream = ffmpeg.output(
            input_stream,
            str(output_path),
            acodec="pcm_s16le",
            ar=TARGET_SAMPLE_RATE,
            ac=1,
            loglevel="error",
        )
        ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
    finally:
        temp_path.unlink(missing_ok=True)

    return str(output_path)


def audio_duration_seconds(wav_path: str) -> float:
    return ami_audio_duration(wav_path)
