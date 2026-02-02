"""Utility script for transcribing audio files using the AZC APIM hosted Azure OpenAI endpoint.

Prerequisites:
    - Azure CLI installed and logged-in
      `az login --scope api://api.azc.test.communities.gov.uk/.default`)
    - `openai` package installed (`python3 -m pip install --user openai`)
    - Audio file to transcribe (supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI


DEPLOYMENT_ID = "minute-gpt4o-transcribe"  # Replace with your audio transcription deployment ID
API_VERSION = "2024-10-21"
TOKEN_SCOPE = "api://api.azc.test.communities.gov.uk/.default"
SUBSCRIPTION_KEY = "a494361198724c7296d0786b017988ae"  # Replace with your APIM subscription key
BASE_URL = (
    "https://api.azc.test.communities.gov.uk/"
    "minute/openai001"
)


def get_access_token() -> str:
    """Fetch an AAD token using an env override or Azure CLI."""
    env_token = (
        os.getenv("APIM_ACCESS_TOKEN")
        or os.getenv("APIM_BEARER_TOKEN")
        or os.getenv("AZ_ACCESS_TOKEN")
    )
    if env_token:
        return env_token.strip()

    if shutil.which("az") is None:
        raise RuntimeError(
            "Azure CLI is not available and no access token override was provided. "
            "Install Azure CLI or export APIM_ACCESS_TOKEN with a valid bearer token."
        )

    command = [
        "az",
        "account",
        "get-access-token",
        "--scope",
        TOKEN_SCOPE,
        "--output",
        "json",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print("Failed to fetch access token via Azure CLI.", file=sys.stderr)
        print(exc.stderr.strip(), file=sys.stderr)
        print(
            "Run `az login --scope "
            f"{TOKEN_SCOPE}` or export APIM_ACCESS_TOKEN before executing this script.",
            file=sys.stderr,
        )
        raise

    payload = json.loads(result.stdout)
    return payload["accessToken"]


def build_client(access_token: str) -> OpenAI:
    """Create an OpenAI client configured for APIM + Azure OpenAI."""
    return OpenAI(
        base_url=f"{BASE_URL}/deployments/{DEPLOYMENT_ID}",
        # Use the bearer token for Authorization and send the APIM subscription key
        # explicitly so APIM's subscription check succeeds.
        api_key=access_token,
        default_headers={
            "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        },
    )


def transcribe_audio(
    client: OpenAI,
    audio_file_path: str,
    language: str | None = None,
    prompt: str | None = None,
    response_format: str = "json",
    temperature: float = 0,
) -> Any:
    """Transcribe an audio file using the Whisper deployment.
    
    Args:
        client: Configured OpenAI client
        audio_file_path: Path to the audio file to transcribe
        language: Optional ISO-639-1 language code (e.g., 'en', 'es')
        prompt: Optional text to guide the model's style
        response_format: Format of the transcript output (json, text, srt, verbose_json, vtt)
        temperature: Sampling temperature (0-1)
    
    Returns:
        Transcription result
    """
    audio_path = Path(audio_file_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    # Check file extension
    valid_extensions = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}
    if audio_path.suffix.lower() not in valid_extensions:
        print(
            f"Warning: File extension {audio_path.suffix} may not be supported. "
            f"Valid extensions: {', '.join(valid_extensions)}",
            file=sys.stderr,
        )
    
    with open(audio_file_path, "rb") as audio_file:
        # Build parameters
        params = {
            "model": DEPLOYMENT_ID,
            "file": audio_file,
            "response_format": response_format,
            "temperature": temperature,
        }
        
        if language:
            params["language"] = language
        
        if prompt:
            params["prompt"] = prompt
        
        # Make the transcription request
        # The extra_query parameter adds the api-version to the URL
        return client.audio.transcriptions.create(
            **params,
            extra_query={"api-version": API_VERSION},
        )


def main() -> None:
    """Main entry point for the transcription script."""
    if len(sys.argv) < 2:
        print("Usage: python transcribe_audio.py <audio_file_path> [language] [prompt]")
        print("\nExamples:")
        print("  python transcribe_audio.py recording.mp3")
        print("  python transcribe_audio.py recording.wav en")
        print("  python transcribe_audio.py recording.m4a en 'Meeting transcription'")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None
    prompt = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Transcribing audio file: {audio_file_path}")
    if language:
        print(f"Language: {language}")
    if prompt:
        print(f"Prompt: {prompt}")
    
    token = get_access_token()
    client = build_client(token)
    
    result = transcribe_audio(
        client,
        audio_file_path,
        language=language,
        prompt=prompt,
        response_format="verbose_json",  # Returns more metadata
    )
    
    print("\n" + "=" * 80)
    print("TRANSCRIPTION RESULT")
    print("=" * 80)
    
    # Handle different response formats
    if hasattr(result, 'text'):
        print(f"\nText: {result.text}")
        
        if hasattr(result, 'language'):
            print(f"Detected Language: {result.language}")
        
        if hasattr(result, 'duration'):
            print(f"Duration: {result.duration}s")
        
        if hasattr(result, 'segments'):
            print(f"\nSegments ({len(result.segments)}):")
            for i, segment in enumerate(result.segments, 1):
                print(f"\n  Segment {i}:")
                print(f"    Time: {segment.start:.2f}s - {segment.end:.2f}s")
                print(f"    Text: {segment.text}")
    else:
        print(result)


if __name__ == "__main__":
    main()