from pathlib import Path
import re
from itertools import product
import subprocess
import ffmpeg
from typing import Dict

from config import FFMPEG_BIN, FFPROBE_BIN 

ConversionOptions = Dict[str, str | list[str]]

BENCHMARK_RE = re.compile(
    r"bench:\s+utime=(?P<utime>[\d.]+)s\s+"
    r"stime=(?P<stime>[\d.]+)s\s+"
    r"rtime=(?P<rtime>[\d.]+)s"
)


def get_audio_duration(path: Path) -> float:
    probe = ffmpeg.probe(str(path), cmd=FFPROBE_BIN)
    return float(probe["format"]["duration"])


def ffmpeg_convert(input_path: Path, output_path: Path, ffmpeg_args: list[str]) -> tuple[Path, Dict[str, int|float]]:
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-benchmark",
        "-i", str(input_path),
        *ffmpeg_args,
        str(output_path),
    ]

    completed = subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    stderr_text = completed.stderr.decode("utf-8", errors="ignore")
    benchmarks = BENCHMARK_RE.search(stderr_text)
    if benchmarks is None:
        raise ValueError("Benchmark regex did not match stderr output")
        
    stderr_text = completed.stderr.decode("utf-8", errors="ignore")
    utime = float(benchmarks.group("utime"))
    stime = float(benchmarks.group("stime"))
    cpu_time = utime + stime

    duration = get_audio_duration(input_path)
    normalised_cpu_time = cpu_time / duration 

    benchmarks_formatted = {
        "utime": utime,
        "stime": stime,
        "cpu_time": utime + stime,
        "duration": duration,
        "normalised_cpu_time": normalised_cpu_time,
        "file_size": output_path.stat().st_size 
    }

    return output_path, benchmarks_formatted


def expand_ffmpeg_dict(spec: ConversionOptions) -> dict[str, list[str]]:
    """
    Converts a dictionary of ffmpeg options into all combinations of
    command-line argument lists.

    Example: 

    Input: 
    {
        "acodec": "flac",
        "compression_level": ["1", "5"],
        "ar": ["8000", "16000"]
    }

    Output: 
    { 
        "acodecflac_compression_level1_ar8000": [
            "-acodec",
            "flac",
            "-compression_level",
            "1",
            "-ar",
            "8000"
        ],
        "acodecflac_compression_level1_ar16000": [
            "-acodec",
            "flac",
            "-compression_level",
            "1",
            "-ar",
            "16000"
        ],
        "acodecflac_compression_level5_ar8000": [
            "-acodec",
            "flac",
            "-compression_level",
            "5",
            "-ar",
            "8000"
        ],
        "acodecflac_compression_level5_ar16000": [
            "-acodec",
            "flac",
            "-compression_level",
            "5",
            "-ar",
            "16000"    
        ]
    }  
    """
    keys = list(spec.keys())
    values = []
    for value in spec.values():
        if isinstance(value, list):
            values.append(value)
        else: 
            values.append([value])

    variants = {}

    for combo in product(*values):
        ffmpeg_args = []
        name_parts = []

        for key, value in zip(keys, combo):
            ffmpeg_args.extend([f"-{key}", value])
            name_parts.append(f"{key}{value}")

        variants["_".join(name_parts)] = ffmpeg_args

    return variants
