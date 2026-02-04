import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
WHISPLY_HF_TOKEN = os.getenv("WHISPLY_HF_TOKEN")
WHISPLY_DEVICE = os.getenv("WHISPLY_DEVICE", "mps")

if not AZURE_SPEECH_KEY:
    raise ValueError("AZURE_SPEECH_KEY not found in environment variables")
if not AZURE_SPEECH_REGION:
    raise ValueError("AZURE_SPEECH_REGION not found in environment variables")
if not WHISPLY_HF_TOKEN:
    raise ValueError("WHISPLY_HF_TOKEN not found in environment variables")

WORKDIR = Path(__file__).parent.parent.parent
AUDIO_DIR = WORKDIR / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

CACHE_DIR = WORKDIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.info("Azure key present: %s", bool(AZURE_SPEECH_KEY))
logger.info("Azure region present: %s", bool(AZURE_SPEECH_REGION))
logger.info("Whisply HF token present: %s", bool(WHISPLY_HF_TOKEN))
logger.info("Whisply device: %s", WHISPLY_DEVICE)
