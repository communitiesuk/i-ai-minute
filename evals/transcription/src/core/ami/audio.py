import logging
from typing import List, cast

import librosa
import numpy

from evals.transcription.src.constants import STEREO_CHANNELS, TARGET_SAMPLE_RATE
from evals.transcription.src.core.ami.types import RawDatasetRow

logger = logging.getLogger(__name__)


def to_mono(audio: numpy.ndarray) -> numpy.ndarray:
    """
    Converts stereo audio to mono by averaging the channels.
    If the audio is already mono, it is returned unchanged.
    """
    if getattr(audio, "ndim", 1) == STEREO_CHANNELS:
        return cast(numpy.ndarray, audio.mean(axis=1))
    return cast(numpy.ndarray, audio)


def resample_if_needed(
    audio: numpy.ndarray,
    current_sample_rate: int,
    target_sample_rate: int = TARGET_SAMPLE_RATE,
) -> numpy.ndarray:
    """
    Resamples the audio to the target sample rate if it is different from the current sample rate.
    """
    if current_sample_rate != target_sample_rate:
        return librosa.resample(audio, orig_sr=current_sample_rate, target_sr=target_sample_rate)
    return cast(numpy.ndarray, audio)


def normalise_peak(audio: numpy.ndarray) -> numpy.ndarray:
    """
    Normalises the audio to ensure the peak amplitude is within [-1.0, 1.0].
    """
    max_val = numpy.abs(audio).max()
    if max_val > 1.0:
        return cast(numpy.ndarray, audio / max_val)
    return cast(numpy.ndarray, audio)


def mix_utterances(
    utterances: List[RawDatasetRow], target_sample_rate: int = TARGET_SAMPLE_RATE
) -> tuple[numpy.ndarray, str]:
    """
    Mixes multiple utterances into a single audio array and concatenates their texts.
    Returns a tuple of (mixed_audio, text).
    """
    if not utterances:
        return numpy.array([], dtype=numpy.float32), ""

    utterances_sorted = sorted(utterances, key=lambda x: x["begin_time"])

    max_end_time = max(utterance["end_time"] for utterance in utterances_sorted)
    total_samples = int(numpy.ceil(max_end_time * target_sample_rate))

    mixed_audio = numpy.zeros(total_samples, dtype=numpy.float32)
    text_parts = []

    for utterance in utterances_sorted:
        audio_array = utterance["audio"]["array"]
        sample_rate = utterance["audio"]["sampling_rate"]
        begin_time = utterance["begin_time"]
        text = utterance["text"]

        audio_array = to_mono(audio_array)
        audio_array = resample_if_needed(audio_array, sample_rate, target_sample_rate)

        start_sample = int(begin_time * target_sample_rate)
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


def compute_duration(audio: numpy.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> float:
    """
    Computes the duration of the audio in seconds.
    """
    return float(len(audio) / sample_rate)
