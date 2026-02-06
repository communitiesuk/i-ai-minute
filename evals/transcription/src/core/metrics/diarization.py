import jiwer

from .transforms import jiwer_transform


def _extract_word_speaker_pairs(segments: list[dict]) -> list[dict]:
    pairs = []
    for seg in segments:
        text = seg.get("text", "")
        if not text:
            continue
        
        words = text.split()
        if not words:
            continue
        
        speaker = seg["speaker"]
        start = seg.get("start", 0)
        end = seg.get("end", 0)
        duration = end - start
        word_duration = duration / len(words)
        
        for i, word in enumerate(words):
            word_start = start + (i * word_duration)
            word_end = word_start + word_duration
            transformed = jiwer_transform([word])[0]
            normalized_word = transformed[0] if transformed else word.lower()
            pairs.append({
                "word": normalized_word,
                "speaker": speaker,
                "start": word_start,
                "end": word_end,
            })
    return pairs


def compute_wder(
    ref_segments: list[dict],
    hyp_segments: list[dict],
) -> dict:
    if not ref_segments or not hyp_segments:
        return {
            "wder": 0.0 if not ref_segments and not hyp_segments else 1.0,
            "speaker_errors": 0,
            "total_words": 0,
            "confusion_count": 0,
        }

    ref_word_speaker_pairs = _extract_word_speaker_pairs(ref_segments)
    hyp_word_speaker_pairs = _extract_word_speaker_pairs(hyp_segments)

    ref_speakers = {p["speaker"] for p in ref_word_speaker_pairs}
    hyp_speakers = {p["speaker"] for p in hyp_word_speaker_pairs}
    
    speaker_mapping = {}
    used_hyp_speakers = set()
    
    for ref_spk in ref_speakers:
        ref_words = {p["word"] for p in ref_word_speaker_pairs if p["speaker"] == ref_spk}
        best_match = None
        best_overlap = 0
        
        for hyp_spk in hyp_speakers:
            if hyp_spk in used_hyp_speakers:
                continue
            hyp_words = {p["word"] for p in hyp_word_speaker_pairs if p["speaker"] == hyp_spk}
            overlap = len(ref_words & hyp_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = hyp_spk
        
        if best_match:
            speaker_mapping[ref_spk] = best_match
            used_hyp_speakers.add(best_match)

    speaker_errors = 0
    total_words = len(ref_word_speaker_pairs)
    matched_hyp_indices = set()

    for ref_pair in ref_word_speaker_pairs:
        expected_hyp_speaker = speaker_mapping.get(ref_pair["speaker"])
        best_match_idx = None
        best_overlap = 0
        
        for idx, hyp_pair in enumerate(hyp_word_speaker_pairs):
            if idx in matched_hyp_indices or hyp_pair["word"] != ref_pair["word"]:
                continue
            
            overlap = max(0, min(ref_pair["end"], hyp_pair["end"]) - max(ref_pair["start"], hyp_pair["start"]))
            if overlap > best_overlap:
                best_overlap = overlap
                best_match_idx = idx
        
        if best_match_idx is not None:
            matched_hyp_indices.add(best_match_idx)
            if hyp_word_speaker_pairs[best_match_idx]["speaker"] != expected_hyp_speaker:
                speaker_errors += 1
        else:
            speaker_errors += 1

    wder = speaker_errors / total_words if total_words > 0 else 0.0
    confusion_count = len(speaker_mapping)

    return {
        "wder": float(wder),
        "speaker_errors": int(speaker_errors),
        "total_words": int(total_words),
        "confusion_count": int(confusion_count),
    }
