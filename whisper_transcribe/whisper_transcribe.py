
import whisper
import torch
from pathlib import Path
import time


def whisper_transcribe(filename):
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = whisper.load_model("small", device=device)

    if device == "mps": 
        model = model.float()

    base_dir = Path(__file__).parent 
    filename =  filename

    audio_path = base_dir / "audio" /filename
   
    start = time.time()
    result = model.transcribe(str(audio_path), fp16=False)
    end = time.time()

    print(f"Time: {end - start:.2f} seconds")
    print(result["text"])



whisper_transcribe("brandon-2x.wav")

