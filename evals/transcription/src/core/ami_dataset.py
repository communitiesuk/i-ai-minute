import logging
from pathlib import Path

from common.audio.ffmpeg import get_duration

from .ami import AMIDatasetLoader

logger = logging.getLogger(__name__)


def load_ami_dataset(
    cache_dir: Path,
    num_samples: int | None,
    sample_duration_fraction: float | None = None,
):
    loader = AMIDatasetLoader(cache_dir, num_samples, sample_duration_fraction)
    samples = loader.prepare()

    if samples:
        _validate_dataset_contract(samples[0])

    return loader


def _validate_dataset_contract(sample: dict):
    if "audio" not in sample:
        msg = "Dataset row must contain 'audio'"
        raise ValueError(msg)
    if "text" not in sample:
        msg = "Dataset row must contain 'text'"
        raise ValueError(msg)
    if "array" not in sample["audio"]:
        msg = "audio must contain 'array'"
        raise ValueError(msg)
    if "sampling_rate" not in sample["audio"]:
        msg = "audio must contain 'sampling_rate'"
        raise ValueError(msg)
    if not isinstance(sample["text"], str):
        msg = "'text' must be a string transcript"
        raise TypeError(msg)

    audio_array = sample["audio"]["array"]
    sampling_rate = sample["audio"]["sampling_rate"]

    logger.info("Dataset contract check passed.")
    logger.debug("Example text type: %s", type(sample["text"]))
    logger.debug("Audio array ndim: %s", getattr(audio_array, "ndim", None))
    logger.debug("Audio array shape: %s", getattr(audio_array, "shape", None))
    logger.debug("Sampling rate: %d", sampling_rate)


def audio_duration_seconds(wav_path: str) -> float:
    return get_duration(Path(wav_path))
