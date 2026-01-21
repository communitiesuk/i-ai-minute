import subprocess
from typing import List

def speed_up(input_path: str, output_path: str, factors: List[float]) -> None:
    # Build the filter chain: "atempo=2.0,atempo=1.5"
    filter_chain = ",".join(f"atempo={f}" for f in factors)

    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-filter:a", filter_chain,
        output_path
    ], check=True)
