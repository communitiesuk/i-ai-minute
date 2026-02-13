import logging
import os

from dotenv import load_dotenv
from eleven_labs.eleven_labs import eleven_text_to_speech, eleven_text_to_speech_with_effects
from transcripts.transcript_util import get_transcripts
from pydub import AudioSegment
from pydub.playback import play
import io
from audio_transformation.audio_effects import mix_audio_with_effects, mp3_to_bytes

def play_audio_bytes(audio_bytes: bytes):
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    play(audio)


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")

if api_key:
    logging.info("Eleven Labs API key found. Using Eleven Labs for audio generation.")
else:
    logging.info("No Eleven Labs API key found. Using a placeholder for audio generation.")


transcript_file = "jordan-alex.txt"

#transcript = get_transcripts(transcript_file)

model_id = "eleven_v3"


#eleven_text_to_speech(api_key or "", transcript, transcript_file, model_id)
# result = eleven_text_to_speech_with_effects(api_key or "", transcript, transcript_file, model_id)


# if result:
#     full_audio, background_effect= result

#     logging.info("Playing background sound effects...")
#     play_audio_bytes(background_effect)
# else:
#     logging.warning("Error generating audio with effects. Skipping playback.")

speech_name, audio_bytes = mp3_to_bytes("eleven_labs/jordan-alex.mp3")
sfx_name, sfx_bytes = mp3_to_bytes("background_sfx/cafe_ambience.mp3")
mix_audio_with_effects(audio_bytes, sfx_bytes, speech_name, sfx_name)