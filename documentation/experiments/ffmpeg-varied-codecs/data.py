from pathlib import Path
from typing import Dict


def get_wav_txt_file_paths(data_dir: Path) -> Dict[Path, Path]: 
    data_dict = {}

    for wav_file in data_dir.glob("*.wav"):
        txt_file = wav_file.with_suffix(".txt")

        if txt_file.exists():
            data_dict[Path(wav_file)] = Path(txt_file)

    return data_dict


def read_txt(txt_path: Path) -> str:
    with open(str(txt_path), "r", encoding="utf-8") as f:
        text = f.read()

    return text
