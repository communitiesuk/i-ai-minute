import logging
from typing import cast

import librosa
import numpy as np

from evals.transcription.src.constants import STEREO_CHANNELS, TARGET_SAMPLE_RATE

logger = logging.getLogger(__name__)


def to_mono(audio: np.ndarray) -> np.ndarray:
    """
    Converts stereo audio to mono by averaging the channels.
    If the audio is already mono, it is returned unchanged.
    """
    if getattr(audio, "ndim", 1) == STEREO_CHANNELS:
        return cast(np.ndarray, audio.mean(axis=1))
    return cast(np.ndarray, audio)


def resample_if_needed(
    audio: np.ndarray,
    sr: int,
    target_sr: int = TARGET_SAMPLE_RATE,
) -> np.ndarray:
    """
    Resamples the audio to the target sample rate if it is different from the original sample rate.
    """
    if sr != target_sr:
        return librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return cast(np.ndarray, audio)


def normalise_peak(audio: np.ndarray) -> np.ndarray:
    """
    Normalises the audio to ensure the peak amplitude is within [-1.0, 1.0].
    """
    max_val = np.abs(audio).max()
    if max_val > 1.0:
        return cast(np.ndarray, audio / max_val)
    return cast(np.ndarray, audio)


def mix_utterances(utterances: list, target_sr: int = TARGET_SAMPLE_RATE) -> tuple[np.ndarray, str]:
    """
    Mixes multiple utterances into a single audio array and concatenates their texts.
    Returns a tuple of (mixed_audio, text).
    """
    if not utterances:
        return np.array([], dtype=np.float32), ""

    utterances_sorted = sorted(utterances, key=lambda x: x.get("begin_time", 0))

    max_end_time = max(utt.get("end_time", 0) for utt in utterances_sorted)
    total_samples = int(np.ceil(max_end_time * target_sr))

    mixed_audio = np.zeros(total_samples, dtype=np.float32)
    text_parts = []

    for utt in utterances_sorted:
        audio_array = utt["audio"]["array"]
        sr = utt["audio"]["sampling_rate"]
        begin_time = utt.get("begin_time", 0)
        text = utt.get("text", "")

        audio_array = to_mono(audio_array)
        audio_array = resample_if_needed(audio_array, sr, target_sr)

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


def compute_duration(audio: np.ndarray, sr: int = TARGET_SAMPLE_RATE) -> float:
    """
    Computes the duration of the audio in seconds.
    """
    return float(len(audio) / sr)
