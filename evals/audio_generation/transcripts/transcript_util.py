from pathlib import Path


def get_transcripts(file_name: str) -> str:
    base_dir = Path(__file__).parent

    transcript_path = base_dir / file_name

    return transcript_path.read_text(encoding="utf-8")
