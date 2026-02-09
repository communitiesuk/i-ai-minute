import logging
from collections import defaultdict
from pathlib import Path
from typing import List

from datasets import load_dataset

from evals.transcription.src.constants import TARGET_SAMPLE_RATE
from evals.transcription.src.core.types import DatasetProtocol
from evals.transcription.src.core.ami import audio, cache
from evals.transcription.src.core.ami.metadata import load_or_build_metadata
from evals.transcription.src.core.ami.selection import MeetingSegment, select_segments
from evals.transcription.src.core.ami.types import AMIDatasetSample
from numpy import ndarray

logger = logging.getLogger(__name__)


def _load_utterances_for_meetings(required_meetings: set, split: str, config: str) -> dict:
    ds = load_dataset("edinburghcstr/ami", config, split=split)
    utterances_by_meeting = defaultdict(list)
    for example in ds:
        meeting_id = example.get("meeting_id", "unknown")
        if meeting_id in required_meetings:
            utterances_by_meeting[meeting_id].append(example)
    return utterances_by_meeting


def _apply_cutoff(utterances: list, cutoff_time: float | None) -> list:
    if cutoff_time is None:
        return utterances

    utterances_sorted = sorted(utterances, key=lambda x: x.get("begin_time", 0))
    result = []
    accumulated = 0.0

    for utt in utterances_sorted:
        duration = utt.get("end_time", 0) - utt.get("begin_time", 0)
        if accumulated + duration <= cutoff_time:
            result.append(utt)
            accumulated += duration
        else:
            break

    return result


def _build_sample(
    mixed_audio: ndarray,  
    text: str,
    segment: MeetingSegment,
    idx: int,
    wav_path: Path,
    num_utterances: int,
) -> AMIDatasetSample:
    return {
        "audio": {
            "array": mixed_audio,
            "sampling_rate": TARGET_SAMPLE_RATE,
            "path": str(wav_path),
        },
        "text": text,
        "meeting_id": segment.meeting_id,
        "dataset_index": idx,
        "duration_sec": audio.compute_duration(mixed_audio),
        "num_utterances": num_utterances,
    }


class AMIDatasetLoader(DatasetProtocol):
    def __init__(
        self,
        cache_dir: Path,
        num_samples: int | None,
        sample_duration_fraction: float | None = None,
        split: str = "train",
        config: str = "ihm",
    ):
        self.cache_dir = cache_dir
        self.num_samples = num_samples
        self.sample_duration_fraction = sample_duration_fraction
        self.split = split
        self.config = config

        self.raw_cache_dir = cache_dir / "raw"
        self.processed_cache_dir = cache_dir / "processed"

        self.raw_cache_dir.mkdir(parents=True, exist_ok=True)
        self.processed_cache_dir.mkdir(parents=True, exist_ok=True)

        self.samples: list[AMIDatasetSample] = []

    def prepare(self) -> list[AMIDatasetSample]:
        metadata = load_or_build_metadata(self.cache_dir, self.split, self.config)
        segments = select_segments(metadata, self.num_samples, self.sample_duration_fraction)

        if not segments:
            logger.warning("No segments selected")
            return []

        utterances_by_meeting = self._load_required_utterances(segments)

        for idx, segment in enumerate(segments):
            sample = self._process_segment(segment, idx, utterances_by_meeting)
            if sample:
                self.samples.append(sample)
                self._log_progress(idx, len(segments))

        logger.info("Dataset preparation complete: %d samples ready", len(self.samples))
        return self.samples

    def _load_required_utterances(self, segments:List[MeetingSegment]) -> dict:   
        all_cached = all(
            cache.get_cache_paths(self.processed_cache_dir, seg, idx).is_complete()
            for idx, seg in enumerate(segments)
        )

        if all_cached:
            logger.info("All required segments are cached, loading from cache...")
            return {}

        logger.info("Loading dataset for selected meetings...")
        required_meetings = {seg.meeting_id for seg in segments}
        return _load_utterances_for_meetings(required_meetings, self.split, self.config)

    def _process_segment(
        self,
        segment: MeetingSegment,
        idx: int,
        utterances_by_meeting: dict,
    ) -> AMIDatasetSample | None:
        paths = cache.get_cache_paths(self.processed_cache_dir, segment, idx)

        if paths.is_complete():
            return self._load_from_cache(paths, segment, idx)

        utterances = utterances_by_meeting.get(segment.meeting_id, [])
        if not utterances:
            logger.warning("No utterances for meeting %s, skipping", segment.meeting_id)
            return None

        return self._build_from_utterances(utterances, paths, segment, idx)

    def _load_from_cache(
        self,
        paths: cache.CachePaths,
        segment: MeetingSegment,
        idx: int,
    ) -> AMIDatasetSample:
        mixed_audio = cache.load_audio(paths.wav)
        text = cache.load_transcript(paths.transcript)
        sample = _build_sample(mixed_audio, text, segment, idx, paths.wav, len(text.split()))

        logger.info(
            "Cache hit: %s (%.2f sec, %d words)",
            segment.meeting_id,
            sample["duration_sec"],
            len(text.split()),
        )
        return sample

    def _build_from_utterances(
        self,
        utterances: list,
        paths: cache.CachePaths,
        segment: MeetingSegment,
        idx: int,
    ) -> AMIDatasetSample:
        utterances = _apply_cutoff(utterances, segment.utterance_cutoff_time)
        mixed_audio, text = audio.mix_utterances(utterances)

        cache.save_audio(paths.wav, mixed_audio)
        cache.save_transcript(paths.transcript, text)

        sample = _build_sample(mixed_audio, text, segment, idx, paths.wav, len(utterances))

        logger.info(
            "Cache miss: mixed %s (%d utterances, %.2f sec, %d words)",
            segment.meeting_id,
            sample["num_utterances"],
            sample["duration_sec"],
            len(text.split()),
        )
        return sample

    def _log_progress(self, idx: int, total: int) -> None:
        if (idx + 1) % 5 == 0 or (idx + 1) == total:
            accumulated = sum(s["duration_sec"] for s in self.samples)
            logger.info("Processed %d/%d segments, %.2f sec total", idx + 1, total, accumulated)

    def __len__(self)-> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> AMIDatasetSample:
        if idx < 0 or idx >= len(self.samples):
            msg = f"Sample index {idx} out of range [0, {len(self.samples)})"
            raise IndexError(msg)
        return self.samples[idx]
