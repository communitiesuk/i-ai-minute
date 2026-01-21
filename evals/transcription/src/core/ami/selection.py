import logging
from dataclasses import dataclass

from .metadata import MeetingMetadata
from .types import MeetingId

logger = logging.getLogger(__name__)


@dataclass
class MeetingSegment:
    meeting_id: MeetingId
    utterance_cutoff_time: float | None = None


def select_segments(metadata: MeetingMetadata, num_samples: float) -> list[MeetingSegment]:
    meeting_ids = metadata["meeting_ids"]
    durations = metadata["durations_sec"]

    if not meeting_ids:
        return []

    if num_samples >= 1.0:
        num_meetings = int(num_samples)
        logger.info("Selecting first %d meetings", num_meetings)
        return [MeetingSegment(meeting_id=mid, utterance_cutoff_time=None) for mid in meeting_ids[:num_meetings]]

    first_meeting_id = meeting_ids[0]
    first_meeting_duration = durations.get(first_meeting_id, 0)
    target_seconds = first_meeting_duration * num_samples

    logger.info("First meeting (%s) duration: %.2f sec", first_meeting_id, first_meeting_duration)
    logger.info(
        "Target total duration: %.2f sec (%.1f%% of first meeting)",
        target_seconds,
        num_samples * 100,
    )

    segments = []
    accumulated = 0.0

    for meeting_id in meeting_ids:
        duration = durations.get(meeting_id, 0)

        if accumulated + duration <= target_seconds:
            segments.append(MeetingSegment(meeting_id=meeting_id, utterance_cutoff_time=None))
            accumulated += duration
            if accumulated >= target_seconds:
                break
        else:
            remaining = target_seconds - accumulated
            if remaining > 0:
                segments.append(MeetingSegment(meeting_id=meeting_id, utterance_cutoff_time=remaining))
            break

    logger.info("Selected %d segments for target %.2f sec", len(segments), target_seconds)
    return segments
