from pathlib import Path

def trim_suffix(filename: str) -> str:
    return Path(filename).stem
