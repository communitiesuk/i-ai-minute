import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

from ...constants import TARGET_SAMPLE_RATE

from .types import MeetingId

logger = logging.getLogger(__name__)


class MeetingMetadata(TypedDict):
    meeting_ids: list[MeetingId]
    durations_sec: dict[MeetingId, float]


def load_or_build_metadata(
    cache_dir: Path,
    split: str = "train",
    config: str = "ihm",
) -> MeetingMetadata:
    metadata_cache_path = cache_dir / "meeting_metadata.json"

    if metadata_cache_path.exists():
        logger.info("Loading cached meeting metadata...")
        with metadata_cache_path.open("r") as f:
            metadata = json.load(f)
        logger.info("Found %d meetings in cache", len(metadata["meeting_ids"]))
        return metadata

    logger.info("Loading AMI dataset (%s configuration)...", config)
    logger.info("This may take a while on first run (downloading full dataset)...")

    ds = load_dataset("edinburghcstr/ami", config, split=split)

    logger.info("Loaded %d utterances from AMI dataset", len(ds))
    logger.info("Grouping utterances by meeting_id and computing durations...")

    meeting_utterances = defaultdict(list)

    for example in ds:
        meeting_id = example.get("meeting_id", "unknown")
        meeting_utterances[meeting_id].append(example)

    logger.info("Found %d unique meetings in dataset", len(meeting_utterances))

    meeting_ids_sorted = sorted(meeting_utterances.keys())
    meeting_durations = {}

    for meeting_id in meeting_ids_sorted:
        utterances = meeting_utterances[meeting_id]
        if utterances:
            max_end_time = max(utt.get("end_time", 0) for utt in utterances)
            meeting_durations[meeting_id] = max_end_time

    metadata: MeetingMetadata = {
        "meeting_ids": meeting_ids_sorted,
        "durations_sec": meeting_durations,
    }

    logger.info("Caching meeting metadata...")
    with metadata_cache_path.open("w") as f:
        json.dump(metadata, f)

    return metadata
