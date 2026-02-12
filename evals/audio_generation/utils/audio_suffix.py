from pathlib import Path

def ensure_mp3_filename(name: str) -> str:
    path = Path(name)
    if path.suffix.lower() != ".mp3":
        path = path.with_suffix(".mp3")
    return str(path)
