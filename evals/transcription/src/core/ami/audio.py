import logging
from typing import List, cast

import librosa
import numpy as np

from evals.transcription.src.constants import STEREO_CHANNELS, TARGET_SAMPLE_RATE
from evals.transcription.src.core.ami.types import RawDatasetRow

logger = logging.getLogger(__name__)


def to_mono(audio: np.ndarray) -> np.ndarray:
    if getattr(audio, "ndim", 1) == STEREO_CHANNELS:
        return cast(np.ndarray, audio.mean(axis=1))
    return cast(np.ndarray, audio)


def resample_if_needed(
    audio: np.ndarray,
    sample_rate: int,
    target_sr: int = TARGET_SAMPLE_RATE,
) -> np.ndarray:
    if sample_rate != target_sr:
        return librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sr)
    return cast(np.ndarray, audio)


def normalise_peak(audio: np.ndarray) -> np.ndarray:
    max_val = np.abs(audio).max()
    if max_val > 1.0:
        return cast(np.ndarray, audio / max_val)
    return cast(np.ndarray, audio)


def mix_utterances(
    utterances: List[RawDatasetRow], target_sr: int = TARGET_SAMPLE_RATE
) -> tuple[np.ndarray, str]:
    if not utterances:
        return np.array([], dtype=np.float32), ""

    utterances_sorted = sorted(utterances, key=lambda x: x["begin_time"])

    max_end_time = max(utterance["end_time"] for utterance in utterances_sorted)
    total_samples = int(np.ceil(max_end_time * target_sr))

    mixed_audio = np.zeros(total_samples, dtype=np.float32)
    text_parts = []

    for utterance in utterances_sorted:
        audio_array = utterance["audio"]["array"]
        sample_rate = utterance["audio"]["sampling_rate"]
        begin_time = utterance["begin_time"]
        text = utterance["text"]

        audio_array = to_mono(audio_array)
        audio_array = resample_if_needed(audio_array, sample_rate, target_sr)

        start_sample = int(begin_time * target_sr)
        end_sample = start_sample + len(audio_array)

        if end_sample > len(mixed_audio):
            end_sample = len(mixed_audio)
            audio_array = audio_array[: end_sample - start_sample]

        mixed_audio[start_sample:end_sample] += audio_array

        if text.strip():
            text_parts.append(text)

    mixed_audio = normalise_peak(mixed_audio)
    full_text = " ".join(text_parts)

    return mixed_audio, full_text


def compute_duration(audio: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> float:
    return float(len(audio) / sample_rate)
