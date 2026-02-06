from pathlib import Path

TARGET_SAMPLE_RATE = 16000
STEREO_CHANNELS = 2

WORKDIR = Path(__file__).resolve().parent
CACHE_DIR = WORKDIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
AUDIO_DIR = WORKDIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)
