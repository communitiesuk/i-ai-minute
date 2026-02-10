from pathlib import Path

from common.constants import STEREO_CHANNELS, TARGET_SAMPLE_RATE

WORKDIR = Path(__file__).resolve().parent
CACHE_DIR = WORKDIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)
AUDIO_DIR = WORKDIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)
