import inspect
from pathlib import Path


def save_audio(full_audio: bytes, output_file: str):
    # Get the file path of the module that called this function
    caller_frame = inspect.stack()[1]
    caller_file = Path(caller_frame.filename)
    caller_dir = caller_file.parent


    audio_dir = caller_dir / "generated_audio_files" 
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Ensure .mp3 extension
    path = audio_dir / output_file
    if path.suffix == "":
        path = path.with_suffix(".mp3")

    path.write_bytes(full_audio)
    return str(path)
