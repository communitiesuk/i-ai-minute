import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if not AZURE_SPEECH_KEY:
    raise ValueError("AZURE_SPEECH_KEY not found in environment variables")
if not AZURE_SPEECH_REGION:
    raise ValueError("AZURE_SPEECH_REGION not found in environment variables")

WORK_DIR =  Path(__file__).parent
DATA_DIR = WORK_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "outputs"

for dir in [DATA_DIR, RAW_DIR, PROCESSED_DIR, OUTPUT_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"
FFPROBE_BIN = "/opt/homebrew/bin/ffprobe"
