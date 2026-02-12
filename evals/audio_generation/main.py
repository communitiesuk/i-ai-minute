import logging
import os

from dotenv import load_dotenv
from eleven_labs.eleven_labs import main
from transcripts.transcript_util import get_transcripts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

load_dotenv()

api_key = os.getenv("ELEVEN_LABS_API_KEY")

if api_key:
    logging.info("Eleven Labs API key found. Using Eleven Labs for audio generation.")
else:
    logging.info("No Eleven Labs API key found. Using a placeholder for audio generation.")


transcript_file = "jordan-alex.txt"

transcript = get_transcripts(transcript_file)

model_id = "eleven_v3"


main(api_key or "", transcript, transcript_file, model_id)
