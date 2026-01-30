import ffmpeg
import logging
import json
from typing import Dict
from pathlib import Path

from .jiwer import score_transcript
from src.adapters import AzureSTTAdapter
from src.core.config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, CACHE_DIR


SPEEDS = [1, 1.2, 1.5] # only values between 0.5 and 2.0

logger = logging.getLogger(__name__)


def speed_audio(input_path: Path, speed: float = 1) -> Path:
    output_directory = CACHE_DIR / 'sped_up_audio'
    output_directory.mkdir(parents=True, exist_ok=True)

    output_file = output_directory / f"{input_path.stem}_{speed}x.wav"
    if output_file.exists(): return output_file

    if not 0.5 <= speed <= 2.0:
        raise ValueError("ffmpeg atempo supports speeds between 0.5 and 2.0")

    ( 
        ffmpeg
        .input(str(input_path))
        .audio.filter("atempo", speed)
        .output(str(output_file))
        .run(overwrite_output=True, quiet=True)
    )

    return output_file

def get_audio_duration(path: Path) -> float:
    probe = ffmpeg.probe(str(path))
    return float(probe["format"]["duration"])

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

def main() -> None: 
    if not (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION):
        raise ValueError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set")

    azureTTS = AzureSTTAdapter(
        speech_key=AZURE_SPEECH_KEY,
        speech_region=AZURE_SPEECH_REGION,
        language="en-GB",
    )

    audio_samples = get_wav_txt_file_paths(CACHE_DIR / 'processed')
    results = {
        'meta': {
            'speeds': SPEEDS,
            'files': [str(path.name) for path in audio_samples]
        },
        'data': {}
    }

    for wav_path, txt_path in audio_samples.items():
        logging.info(f'Processing {wav_path.name}')
        reference = read_txt(txt_path)

        results['data'][wav_path.stem] = {}
        
        for speed in SPEEDS: 
            try:
                sped_audio = speed_audio(wav_path, speed)
                text, proc_time, _ = azureTTS.transcribe_with_debug(str(sped_audio))

                results['data'][wav_path.stem][f'{speed}x_speed'] = {
                    'meta': {
                        'duration': get_audio_duration(sped_audio),
                        'proc_time': proc_time
                        },
                    'score': score_transcript(reference, text)
                }
            except Exception as e:
                logging.error(f'Failed at {wav_path.name} ({speed}x): {e}')

        with open("output.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()