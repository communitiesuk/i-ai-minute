from pathlib import Path
import pandas as pd
from typing import Dict
import json
from config import (
    OUTPUT_DIR, PROCESSED_DIR, 
    AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
    )
from ffmpeg_utils import ConversionOptions, ffmpeg_convert, expand_ffmpeg_dict
from transcribe import AzureSTT
from jiwer_utils import score_transcript
from data import read_txt


if not AZURE_SPEECH_KEY:
    raise ValueError("AZURE_SPEECH_KEY not found in environment variables")
if not AZURE_SPEECH_REGION:
    raise ValueError("AZURE_SPEECH_REGION not found in environment variables")

azureTTS = AzureSTT(
    speech_key=AZURE_SPEECH_KEY,
    speech_region=AZURE_SPEECH_REGION,
    language="en-GB",
)

def run_codec_benchmarks(
        combination_codecs: Dict[str, ConversionOptions], 
        standalone_codecs: Dict[str, list[ConversionOptions]],
        audio_samples: Dict[Path, Path],
        results_output_path: Path = OUTPUT_DIR / "codec_benchmarks.json",
        with_transcription = True
        ):
    codecs = set(list(combination_codecs.keys()) + list(standalone_codecs.keys()))
    for codec in codecs:
        (PROCESSED_DIR / codec).mkdir(parents=True, exist_ok=True)

    # Produce Benchmarks
    results = {
        "meta": {
            "files": {},
            "codecs": []
        },
        "data": {}
    }

    for codec in codecs:
        print(f"Codec: {codec}")

        results["data"][codec] = {}
        variants = {}
        if codec in combination_codecs:
            variants = variants | expand_ffmpeg_dict(combination_codecs[codec])
        if codec in standalone_codecs:
            for spec in standalone_codecs[codec]:
                variants = variants | expand_ffmpeg_dict(spec)

        for name, args in variants.items():
            print(f"Flags: {name}")

            results["data"][codec][name] = {}
            results["meta"]["codecs"].append(name)

            for sample_path, txt_path in audio_samples.items():
                output_path = (
                    PROCESSED_DIR
                    / codec
                    / f"{sample_path.stem}.{name}.{codec}"
                )

                output_file_path, benchmarks = ffmpeg_convert(
                    sample_path,
                    output_path,
                    args,
                )

                jiwer_scores = {}
                if with_transcription:
                    transcription, _ = azureTTS.transcribe(str(output_file_path))
                    jiwer_scores = score_transcript(read_txt(txt_path), transcription)

                results["data"][codec][name][sample_path.stem] = (
                    benchmarks
                    | jiwer_scores
                    | {"ffmpeg_args": args}
                )
                results["meta"]["files"][sample_path.stem] = {
                    "duration": benchmarks["duration"],
                    "file_size": benchmarks["file_size"]
                }

    # save outputs
    with open(results_output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Written outputs to {results_output_path}")

    return results


def codec_json_to_df(json_path: Path) -> pd.DataFrame:
    # Convert JSON to dataframe
    with open(json_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    rows = []

    for codec, specs in results["data"].items():
        for spec, files in specs.items():
            for file_id, metrics in files.items():
                row = {
                    "codec": codec,
                    "spec": spec,
                    "file_id": file_id,
                }
                # add all metrics as columns
                row.update(metrics)
                rows.append(row)

    return pd.DataFrame(rows)