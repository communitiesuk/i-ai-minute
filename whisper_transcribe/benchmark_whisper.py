import time
import torch
import whisper
from pathlib import Path

def benchmark(model_name, device, audio_path):
    print(f"\n--- Benchmarking {model_name} on {device} ---")

    # Load model on the chosen device
    model = whisper.load_model(model_name, device=device)

    # Critical fix for MPS instability
    if device == "mps":
        model = model.float()

    start = time.time()
    result = model.transcribe(str(audio_path), fp16=False)
    end = time.time()

    print(f"Time: {end - start:.2f} seconds")
    print(f"Transcript sample: {result['text']}")
    return end - start

def main():
    # Determine available devices
    devices = ["cpu"]
    if torch.backends.mps.is_available():
        devices.append("mps")

    # Models to test
    models = ["tiny", "base", "small"]

    # Resolve audio path relative to this script
    base_dir = Path(__file__).parent
    filename = "brandon-2x.wav"
    audio_path = base_dir / "audio" / filename

    # Run benchmarks
    for model_name in models:
        for device in devices:
            benchmark(model_name, device, audio_path)

if __name__ == "__main__":
    main()
