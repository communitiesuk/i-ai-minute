from pathlib import Path
import inspect

def save_audio(full_audio: bytes, output_file: str):
    # Get the file path of the module that called this function
    caller_frame = inspect.stack()[1]
    caller_file = Path(caller_frame.filename)
    caller_dir = caller_file.parent

    # Ensure .mp3 extension
    path = caller_dir / output_file
    if path.suffix == "":
        path = path.with_suffix(".mp3")

    path.write_bytes(full_audio)
    return str(path)
