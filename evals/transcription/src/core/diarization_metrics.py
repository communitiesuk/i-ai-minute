import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def align_speaker_labels(ref_segments: list[dict], hyp_segments: list[dict]) -> list[dict]:
    """
    Align hypothesis speaker labels to reference speaker labels based on temporal overlap.
    
    This is necessary because different diarization systems use different speaker labels
    (e.g., "Speaker_1" vs "SPEAKER_00"). We map hypothesis speakers to reference speakers
    by finding which reference speaker they overlap with most.
    
    Args:
        ref_segments: Reference diarization segments
        hyp_segments: Hypothesis diarization segments
    
    Returns:
        New hypothesis segments with aligned speaker labels
    """
    if not ref_segments or not hyp_segments:
        return hyp_segments
    
    ref_speakers = set(seg["speaker"] for seg in ref_segments)
    hyp_speakers = set(seg["speaker"] for seg in hyp_segments)
    
    overlap_matrix = {}
    
    for hyp_speaker in hyp_speakers:
        overlap_matrix[hyp_speaker] = {}
        
        for ref_speaker in ref_speakers:
            overlap_matrix[hyp_speaker][ref_speaker] = 0.0
    
    for hyp_seg in hyp_segments:
        hyp_speaker = hyp_seg["speaker"]
        hyp_start = hyp_seg["start"]
        hyp_end = hyp_seg["end"]
        
        for ref_seg in ref_segments:
            ref_speaker = ref_seg["speaker"]
            ref_start = ref_seg["start"]
            ref_end = ref_seg["end"]
            
            overlap_start = max(hyp_start, ref_start)
            overlap_end = min(hyp_end, ref_end)
            
            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                overlap_matrix[hyp_speaker][ref_speaker] += overlap_duration
    
    speaker_mapping = {}
    used_ref_speakers = set()
    
    sorted_hyp_speakers = sorted(
        hyp_speakers,
        key=lambda hs: max(overlap_matrix[hs].values()) if overlap_matrix[hs] else 0,
        reverse=True
    )
    
    for hyp_speaker in sorted_hyp_speakers:
        overlaps = overlap_matrix[hyp_speaker]
        
        available_overlaps = {
            ref_sp: duration 
            for ref_sp, duration in overlaps.items() 
            if ref_sp not in used_ref_speakers
        }
        
        if available_overlaps:
            best_ref_speaker = max(available_overlaps, key=available_overlaps.get)
            speaker_mapping[hyp_speaker] = best_ref_speaker
            used_ref_speakers.add(best_ref_speaker)
        else:
            speaker_mapping[hyp_speaker] = hyp_speaker
    
    aligned_segments = []
    for seg in hyp_segments:
        aligned_seg = seg.copy()
        aligned_seg["speaker"] = speaker_mapping.get(seg["speaker"], seg["speaker"])
        aligned_seg["original_speaker"] = seg["speaker"]
        aligned_segments.append(aligned_seg)
    
    logger.info("Speaker label alignment: %s", speaker_mapping)
    
    return aligned_segments


def compute_der(
    ref_segments: list[dict],
    hyp_segments: list[dict],
    collar: float = 0.25,
    ignore_overlaps: bool = False,
) -> dict:
    """
    Compute Diarization Error Rate (DER).
    
    DER = (Miss + False Alarm + Confusion) / Total Reference Time
    
    Args:
        ref_segments: Reference diarization segments with 'start', 'end', 'speaker'
        hyp_segments: Hypothesis diarization segments with 'start', 'end', 'speaker'
        collar: Tolerance collar in seconds (default 0.25s)
        ignore_overlaps: Whether to ignore overlapping speech regions
    
    Returns:
        Dictionary with DER components and total
    """
    if not ref_segments:
        return {
            "der": 100.0 if hyp_segments else 0.0,
            "miss": 0.0,
            "false_alarm": 100.0 if hyp_segments else 0.0,
            "confusion": 0.0,
            "total_ref_time": 0.0,
            "scored_time": 0.0,
        }
    
    total_ref_time = sum(seg["end"] - seg["start"] for seg in ref_segments)
    
    if total_ref_time == 0:
        return {
            "der": 0.0,
            "miss": 0.0,
            "false_alarm": 0.0,
            "confusion": 0.0,
            "total_ref_time": 0.0,
            "scored_time": 0.0,
        }
    
    miss_time = 0.0
    false_alarm_time = 0.0
    confusion_time = 0.0
    
    ref_timeline = _build_timeline(ref_segments, collar)
    hyp_timeline = _build_timeline(hyp_segments, collar)
    
    all_times = sorted(set(ref_timeline.keys()) | set(hyp_timeline.keys()))
    
    for i in range(len(all_times) - 1):
        t_start = all_times[i]
        t_end = all_times[i + 1]
        duration = t_end - t_start
        
        if duration <= 0:
            continue
        
        ref_speakers = ref_timeline.get(t_start, set())
        hyp_speakers = hyp_timeline.get(t_start, set())
        
        if ignore_overlaps and (len(ref_speakers) > 1 or len(hyp_speakers) > 1):
            continue
        
        if not ref_speakers and hyp_speakers:
            false_alarm_time += duration
        elif ref_speakers and not hyp_speakers:
            miss_time += duration
        elif ref_speakers and hyp_speakers:
            if ref_speakers != hyp_speakers:
                confusion_time += duration
    
    scored_time = total_ref_time
    
    miss_rate = (miss_time / scored_time * 100.0) if scored_time > 0 else 0.0
    fa_rate = (false_alarm_time / scored_time * 100.0) if scored_time > 0 else 0.0
    confusion_rate = (confusion_time / scored_time * 100.0) if scored_time > 0 else 0.0
    
    der = miss_rate + fa_rate + confusion_rate
    
    return {
        "der": der,
        "miss": miss_rate,
        "false_alarm": fa_rate,
        "confusion": confusion_rate,
        "total_ref_time": total_ref_time,
        "scored_time": scored_time,
        "miss_time": miss_time,
        "false_alarm_time": false_alarm_time,
        "confusion_time": confusion_time,
    }


def compute_jer(ref_segments: list[dict], hyp_segments: list[dict]) -> dict:
    """
    Compute Jaccard Error Rate (JER).
    
    JER = 1 - (sum of IoU per speaker) / number of speakers
    
    Args:
        ref_segments: Reference diarization segments
        hyp_segments: Hypothesis diarization segments
    
    Returns:
        Dictionary with JER and per-speaker IoU
    """
    if not ref_segments or not hyp_segments:
        return {
            "jer": 100.0,
            "jaccard_index": 0.0,
            "per_speaker_iou": {},
        }
    
    ref_speakers = set(seg["speaker"] for seg in ref_segments)
    hyp_speakers = set(seg["speaker"] for seg in hyp_segments)
    all_speakers = ref_speakers | hyp_speakers
    
    per_speaker_iou = {}
    total_iou = 0.0
    
    for speaker in all_speakers:
        ref_intervals = [
            (seg["start"], seg["end"])
            for seg in ref_segments
            if seg["speaker"] == speaker
        ]
        hyp_intervals = [
            (seg["start"], seg["end"])
            for seg in hyp_segments
            if seg["speaker"] == speaker
        ]
        
        intersection = _compute_interval_intersection(ref_intervals, hyp_intervals)
        union = _compute_interval_union(ref_intervals, hyp_intervals)
        
        iou = (intersection / union) if union > 0 else 0.0
        per_speaker_iou[speaker] = iou
        total_iou += iou
    
    jaccard_index = (total_iou / len(all_speakers)) if all_speakers else 0.0
    jer = (1.0 - jaccard_index) * 100.0
    
    return {
        "jer": jer,
        "jaccard_index": jaccard_index,
        "per_speaker_iou": per_speaker_iou,
        "num_speakers": len(all_speakers),
    }


def compute_speaker_count_error(ref_segments: list[dict], hyp_segments: list[dict]) -> dict:
    """
    Compute speaker count error metrics.
    
    Args:
        ref_segments: Reference diarization segments
        hyp_segments: Hypothesis diarization segments
    
    Returns:
        Dictionary with speaker count metrics
    """
    ref_speakers = set(seg["speaker"] for seg in ref_segments) if ref_segments else set()
    hyp_speakers = set(seg["speaker"] for seg in hyp_segments) if hyp_segments else set()
    
    ref_count = len(ref_speakers)
    hyp_count = len(hyp_speakers)
    
    absolute_error = abs(hyp_count - ref_count)
    bias = hyp_count - ref_count
    
    relative_error = (absolute_error / ref_count * 100.0) if ref_count > 0 else 0.0
    
    return {
        "ref_speaker_count": ref_count,
        "hyp_speaker_count": hyp_count,
        "absolute_error": absolute_error,
        "bias": bias,
        "relative_error": relative_error,
        "is_overestimated": bias > 0,
        "is_underestimated": bias < 0,
        "is_correct": bias == 0,
    }


def compute_all_diarization_metrics(
    ref_segments: list[dict],
    hyp_segments: list[dict],
    collar: float = 0.25,
    ignore_overlaps: bool = False,
) -> dict:
    """
    Compute all diarization metrics.
    
    Automatically aligns hypothesis speaker labels to reference labels before computing metrics.
    
    Args:
        ref_segments: Reference diarization segments
        hyp_segments: Hypothesis diarization segments
        collar: DER collar tolerance in seconds
        ignore_overlaps: Whether to ignore overlapping speech in DER
    
    Returns:
        Dictionary with all metrics
    """
    aligned_hyp_segments = align_speaker_labels(ref_segments, hyp_segments)
    
    der_metrics = compute_der(ref_segments, aligned_hyp_segments, collar, ignore_overlaps)
    jer_metrics = compute_jer(ref_segments, aligned_hyp_segments)
    speaker_count_metrics = compute_speaker_count_error(ref_segments, hyp_segments)
    
    return {
        "der": der_metrics,
        "jer": jer_metrics,
        "speaker_count": speaker_count_metrics,
        "component_breakdown": {
            "miss": der_metrics["miss"],
            "false_alarm": der_metrics["false_alarm"],
            "confusion": der_metrics["confusion"],
        },
        "speaker_mapping": {
            seg["original_speaker"]: seg["speaker"] 
            for seg in aligned_hyp_segments 
            if "original_speaker" in seg
        } if aligned_hyp_segments else {},
    }


def _build_timeline(segments: list[dict], collar: float = 0.0) -> dict:
    """
    Build a timeline mapping time points to active speakers.
    
    Args:
        segments: Diarization segments
        collar: Collar to apply to segment boundaries
    
    Returns:
        Dictionary mapping time points to sets of active speakers
    """
    events = []
    
    for seg in segments:
        start = max(0, seg["start"] - collar)
        end = seg["end"] + collar
        speaker = seg["speaker"]
        
        events.append((start, "start", speaker))
        events.append((end, "end", speaker))
    
    events.sort(key=lambda x: (x[0], x[1] == "end"))
    
    timeline = {}
    active_speakers = set()
    
    for time, event_type, speaker in events:
        if event_type == "start":
            active_speakers.add(speaker)
        else:
            active_speakers.discard(speaker)
        
        timeline[time] = active_speakers.copy()
    
    return timeline


def _compute_interval_intersection(intervals1: list[tuple], intervals2: list[tuple]) -> float:
    """Compute total intersection duration between two sets of intervals."""
    total = 0.0
    
    for start1, end1 in intervals1:
        for start2, end2 in intervals2:
            overlap_start = max(start1, start2)
            overlap_end = min(end1, end2)
            
            if overlap_start < overlap_end:
                total += overlap_end - overlap_start
    
    return total


def _compute_interval_union(intervals1: list[tuple], intervals2: list[tuple]) -> float:
    """Compute total union duration between two sets of intervals."""
    all_intervals = intervals1 + intervals2
    
    if not all_intervals:
        return 0.0
    
    all_intervals = sorted(all_intervals)
    
    merged = []
    current_start, current_end = all_intervals[0]
    
    for start, end in all_intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end
    
    merged.append((current_start, current_end))
    
    return sum(end - start for start, end in merged)
