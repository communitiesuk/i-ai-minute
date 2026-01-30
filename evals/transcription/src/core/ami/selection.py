import logging
from dataclasses import dataclass

from .metadata import MeetingMetadata
from .types import MeetingId

logger = logging.getLogger(__name__)


@dataclass
class MeetingSegment:
    meeting_id: MeetingId
    utterance_cutoff_time: float | None = None


def select_segments(metadata: MeetingMetadata, num_samples: int | None, sample_duration_fraction: float | None = None) -> list[MeetingSegment]:
    meeting_ids = metadata["meeting_ids"]
    durations = metadata["durations_sec"]

    if not meeting_ids:
        return []

    num_meetings = len(meeting_ids) if num_samples is None else num_samples
    
    if sample_duration_fraction is not None:
        logger.info("Selecting first %d meetings with %.1f%% duration each", num_meetings, sample_duration_fraction * 100)
        
        segments = []
        for mid in meeting_ids[:num_meetings]:
            meeting_duration = durations.get(mid, 0)
            cutoff_time = meeting_duration * sample_duration_fraction
            segments.append(MeetingSegment(meeting_id=mid, utterance_cutoff_time=cutoff_time))
        
        return segments

    logger.info("Selecting first %d meetings", num_meetings)
    return [MeetingSegment(meeting_id=mid, utterance_cutoff_time=None) for mid in meeting_ids[:num_meetings]]
