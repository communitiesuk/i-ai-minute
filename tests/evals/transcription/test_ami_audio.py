from __future__ import annotations

import numpy as np

from evals.transcription.src.core.ami import audio
from evals.transcription.src.core.ami.loader import _apply_cutoff
from evals.transcription.src.models import RawAudioDict, RawDatasetRow


def test_mix_utterances_aligns_and_concatenates_text():
    utterances = [
        RawDatasetRow(
            meeting_id="test",
            audio_id="1",
            text="hello",
            audio=RawAudioDict(array=np.array([0.5, 0.5], dtype=np.float32), sampling_rate=16000),
            begin_time=0.0,
            end_time=2 / 16000,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
        RawDatasetRow(
            meeting_id="test",
            audio_id="2",
            text="world",
            audio=RawAudioDict(array=np.array([0.25, 0.25], dtype=np.float32), sampling_rate=16000),
            begin_time=2 / 16000,
            end_time=4 / 16000,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
    ]

    mixed, text = audio.mix_utterances(utterances, target_sample_rate=16000)

    assert text == "hello world"
    assert len(mixed) == 4
    np.testing.assert_allclose(mixed, np.array([0.5, 0.5, 0.25, 0.25], dtype=np.float32))


def test_mix_utterances_overlaps_and_normalises_peak():
    utterances = [
        RawDatasetRow(
            meeting_id="test",
            audio_id="1",
            text="one",
            audio=RawAudioDict(array=np.array([1.0, 1.0], dtype=np.float32), sampling_rate=16000),
            begin_time=0.0,
            end_time=2 / 16000,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
        RawDatasetRow(
            meeting_id="test",
            audio_id="2",
            text="two",
            audio=RawAudioDict(array=np.array([1.0, 1.0], dtype=np.float32), sampling_rate=16000),
            begin_time=0.0,
            end_time=2 / 16000,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
    ]

    mixed, _text = audio.mix_utterances(utterances, target_sample_rate=16000)

    np.testing.assert_allclose(mixed, np.array([2.0, 2.0], dtype=np.float32))


def test_apply_cutoff_respects_duration():
    utterances = [
        RawDatasetRow(
            meeting_id="test",
            audio_id="1",
            text="a",
            audio=RawAudioDict(array=np.array([0.0], dtype=np.float32), sampling_rate=16000),
            begin_time=0.0,
            end_time=1.0,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
        RawDatasetRow(
            meeting_id="test",
            audio_id="2",
            text="b",
            audio=RawAudioDict(array=np.array([0.0], dtype=np.float32), sampling_rate=16000),
            begin_time=1.0,
            end_time=2.5,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
        RawDatasetRow(
            meeting_id="test",
            audio_id="3",
            text="c",
            audio=RawAudioDict(array=np.array([0.0], dtype=np.float32), sampling_rate=16000),
            begin_time=2.5,
            end_time=4.0,
            microphone_id="mic1",
            speaker_id="spk1",
        ),
    ]

    trimmed = _apply_cutoff(utterances, cutoff_time=2.0)

    assert [u.text for u in trimmed] == ["a"]
