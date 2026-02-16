import time
from pathlib import Path
import httpx
from typing import Any


class AzureSTT:
    def __init__(self, speech_key: str, speech_region: str, language: str = "en-GB"):
        if not speech_key or not speech_region:
            raise ValueError("Azure speech key and region are required")
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.language = language
        self.url = f"https://{speech_region}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe"


    def transcribe(self, wav_path: str) -> tuple[str, float]:
        text, proc_sec, _ = self.transcribe_with_debug(wav_path)
        return text, proc_sec
    

    def transcribe_with_debug(self, wav_path: str) -> tuple[str, float, dict[str, Any]]:
        t0 = time.time()

        with open(wav_path, "rb") as audio_file:
            audio_content = audio_file.read()
            files = {
                "audio": (f"audio{Path(wav_path).suffix}", audio_content),
                "definition": (
                    None,
                    f'{{"locales":["{self.language}"],"diarization":{{"enabled":true}},"profanityFilterMode":"None"}}',
                ),
            }

        headers = {"Ocp-Apim-Subscription-Key": self.speech_key}
        params = {"api-version": "2024-11-15"}

        timeout_settings = httpx.Timeout(
            timeout=900.0,
            connect=900.0,
            read=900.0,
            write=900.0,
        )

        try:
            with httpx.Client(timeout=timeout_settings) as client:
                response = client.post(self.url, headers=headers, files=files, params=params)
                response.raise_for_status()
                full_response = response.json()
        except httpx.HTTPError as e:
            t1 = time.time()
            return "", (t1 - t0), {"error": str(e)}

        t1 = time.time()

        if "code" in full_response:
            error_message = full_response.get("message", "Unknown error occurred")
            return "", (t1 - t0), {"error": error_message}

        phrases = full_response.get("phrases", [])
        if not phrases:
            return "", (t1 - t0), {"error": "No phrases found"}

        full_text = " ".join(phrase["text"] for phrase in phrases).strip()

        debug = {
            "mode": "post_api",
            "recognized_segments": len(phrases),
            "final_text_len_chars": len(full_text),
        }

        return full_text, (t1 - t0), debug
