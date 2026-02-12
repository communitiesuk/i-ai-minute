import logging
import re

from elevenlabs.client import ElevenLabs
from utils.build_pattern import build_pattern
from utils.extract_speakers import extract_speakers
from utils.save_audio import save_audio
from utils.select_voice import get_voice_for_speaker
from utils.trim_suffix import trim_suffix

logger = logging.getLogger(__name__)


def main(api_key: str, transcript_content: str, transcript_file: str, model_id: str):
    if not api_key:
        logger.warning("No Eleven Labs API key provided. Audio generation will be skipped.")
        return

    client = ElevenLabs(api_key=api_key) if api_key else None

    speakers = extract_speakers(transcript_content)
    pattern = build_pattern(speakers)
    chunks = re.findall(pattern, transcript_content, flags=re.S)

    audio_segments = []
    for speaker, text, _ in chunks:
        voice_id = get_voice_for_speaker(speaker)

        audio = client.text_to_speech.convert(  # type: ignore
            text=text.strip(),
            voice_id=voice_id if voice_id else "JBFqnCBsd6RMkjVDRZzb",
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio)
        audio_segments.append(audio_bytes)

    # Combine audio
    full_audio = b"".join(audio_segments)

    # Trim file name to create output file name
    output_file = trim_suffix(transcript_file) + ".mp3"

    # Save to file
    saved_path = save_audio(full_audio, output_file)
    logger.info(f"Audio saved to {saved_path}")
