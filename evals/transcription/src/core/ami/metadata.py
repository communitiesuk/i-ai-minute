import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import TypedDict, cast

from datasets import load_dataset

from evals.transcription.src.core.ami import AMI_DATASET_NAME

logger = logging.getLogger(__name__)


class MeetingMetadata(TypedDict):
    """
    Metadata containing meeting IDs and their durations.
    """

    meeting_ids: list[str]
    durations_sec: dict[str, float]


def load_or_build_metadata(
    cache_dir: Path,
    split: str = "train",
    config: str = "ihm",
) -> MeetingMetadata:
    """
    Loads meeting metadata from cache if available, otherwise builds it by loading the AMI
    dataset and extracting meeting IDs and durations.
    """
    metadata_cache_path = cache_dir / "meeting_metadata.json"

    if metadata_cache_path.exists():
        logger.info("Loading cached meeting metadata...")
        with metadata_cache_path.open("r") as file_handle:
            metadata = json.load(file_handle)
        logger.info("Found %d meetings in cache", len(metadata["meeting_ids"]))
        return cast(MeetingMetadata, metadata)

    logger.info("Loading AMI dataset (%s configuration)...", config)
    logger.info("This may take a while on first run (downloading full dataset)...")

    dataset = load_dataset(AMI_DATASET_NAME, config, split=split)

    logger.info("Loaded %d utterances from AMI dataset", len(dataset))
    logger.info("Grouping utterances by meeting_id and computing durations...")

    meeting_utterances = defaultdict(list)

    for example in dataset:
        meeting_id = example.get("meeting_id", "unknown")
        meeting_utterances[meeting_id].append(example)

    logger.info("Found %d unique meetings in dataset", len(meeting_utterances))

    meeting_ids_sorted = sorted(meeting_utterances.keys())
    meeting_durations = {}

    for meeting_id in meeting_ids_sorted:
        utterances = meeting_utterances[meeting_id]
        if utterances:
            max_end_time = max(utterance.get("end_time", 0) for utterance in utterances)
            meeting_durations[meeting_id] = max_end_time

    new_metadata: MeetingMetadata = {
        "meeting_ids": meeting_ids_sorted,
        "durations_sec": meeting_durations,
    }

    logger.info("Caching meeting metadata...")
    with metadata_cache_path.open("w") as file_handle:
        json.dump(new_metadata, file_handle)

    return new_metadata
