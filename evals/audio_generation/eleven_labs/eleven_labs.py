
from dotenv import load_dotenv 
from pathlib import Path 
import os
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import logging

import re
from transcripts import get_transcripts
from utils.save_audio import save_audio
from utils.trim_suffix import trim_suffix



logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent / ".env")

eleven_labs_key= os.getenv("ELEVEN_LABS_API_KEY")

if eleven_labs_key:
    logging.info("Eleven Labs API key found. Using Eleven Labs for audio generation.")
else:
     logging.info("No Eleven Labs API key found. Using a placeholder for audio generation.")   

transcript_file ="two-teens-short.txt"

def main(api_key: str, transcript_file: str):



    client = ElevenLabs(api_key= api_key) if eleven_labs_key else None
    voice_map = { "Teen 1": "JBFqnCBsd6RMkjVDRZzb", "Teen 2": "EXAVITQu4vr4xnSDxMaL" }

    # Parse transcript into (speaker, text) pairs 
    pattern = r"(Teen 1|Teen 2):\s*(.+?)(?=(Teen 1|Teen 2):|$)" 
    chunks = re.findall(pattern, transcript_file, flags=re.S)

    audio_segments = []
    for speaker, text, _ in chunks: 
        voice_id = voice_map.get(speaker) 

        audio = client.text_to_speech.convert( #type: ignore
            text=text.strip(), 
            voice_id=voice_id if voice_id else "JBFqnCBsd6RMkjVDRZzb", 
            model_id="eleven_turbo_v2_5", 
            output_format="mp3_44100_128", 
            ) 
        audio_bytes = b"".join(audio) 
        audio_segments.append(audio_bytes)
    
    # Combines audio  
    full_audio = b"".join(audio_segments) 

    # Trim file name
    output_file = trim_suffix(transcript_file) + ".mp3"


    # Save to file 
    saved_path = save_audio(full_audio, output_file) 
    logger.info(f"Audio saved to {saved_path}")



  






if __name__ == "__main__":
 main()