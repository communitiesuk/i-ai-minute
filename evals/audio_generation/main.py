import io
import logging
import os

from audio_transformation.audio_effects import mix_audio_with_effects, mp3_to_bytes
from dotenv import load_dotenv
from pydub import AudioSegment



logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")

if api_key:
    logging.info("Eleven Labs API key found. Using Eleven Labs for audio generation.")
else:
    logging.info("No Eleven Labs API key found. Using a placeholder for audio generation.")

"""
Set transcript_file to an existing transcript within the 
transcripts dir and select your desired model
"""

transcript_file = "jordan-alex.txt"

# transcript = get_transcripts(transcript_file)

model_id = "eleven_v3"


# eleven_text_to_speech(api_key or "", transcript, transcript_file, model_id)
# result = eleven_text_to_speech_with_effects(api_key or "", transcript, transcript_file, model_id)


# if result:
#     full_audio, background_effect= result

#     logging.info("Playing background sound effects...")
#     play_audio_bytes(background_effect)
# else:
#     logging.warning("Error generating audio with effects. Skipping playback.")


"""
The pattern below can be used to combine stored transcribed audio and 
sound‑effect files into a single mixed audio track.

"""
speech_name, audio_bytes = mp3_to_bytes("eleven_labs/jordan-alex.mp3")
sfx_name, sfx_bytes = mp3_to_bytes("background_sfx/noise_on_a_typical_metro.mp3")
mix_audio_with_effects(audio_bytes, sfx_bytes, speech_name, sfx_name)
