import whisper
import torch
from pathlib import Path
import time
from typing import Dict, Any


device = "mps" if torch.backends.mps.is_available() else "cpu"
_model = whisper.load_model("small", device=device)
if device == "mps": 
    model = _model.float()

    base_dir = Path(__file__).parent 

def transcriber(filename):
    filename =  filename

    audio_path = base_dir / "audio" / filename
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

   
    start = time.time()
    result: Dict[str, Any] = model.transcribe(str(audio_path), fp16=False) 

    end = time.time()

    print(f"Time: {end - start:.2f} seconds")
    return result["text"].strip()



#transcriber("brandon-2x.wav")

