import logging
import threading
import time

import azure.cognitiveservices.speech as speechsdk

from .base import TranscriptionAdapter

logger = logging.getLogger(__name__)


class AzureSTTAdapter(TranscriptionAdapter):
    def __init__(self, speech_key: str, speech_region: str, language: str = "en-US"):
        if not speech_key or not speech_region:
            raise ValueError("Azure speech key and region are required")
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.language = language

    def _make_recogniser(self, wav_path: str):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.speech_region)
        speech_config.speech_recognition_language = self.language

        audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
        recogniser = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        return recogniser

    def transcribe(self, wav_path: str):
        text, proc_sec, _ = self.transcribe_with_debug(wav_path)
        return text, proc_sec

    def transcribe_with_debug(self, wav_path: str):
        recogniser = self._make_recogniser(wav_path)

        parts = []
        error_info = {"canceled": False, "details": None}
        done = threading.Event()

        def on_recognized(evt):
            res = evt.result
            if res.reason == speechsdk.ResultReason.RecognizedSpeech and (res.text or "").strip():
                parts.append(res.text.strip())
            elif res.reason == speechsdk.ResultReason.NoMatch:
                no_match_details = speechsdk.NoMatchDetails(res)
                logger.warning(f"No speech recognized: {no_match_details.reason}")

        def on_canceled(evt):
            cd = speechsdk.CancellationDetails.from_result(evt.result)
            error_info["canceled"] = True
            error_info["details"] = f"{cd.reason}: {cd.error_details}"
            done.set()

        def on_session_stopped(evt):
            done.set()

        recogniser.recognized.connect(on_recognized)
        recogniser.canceled.connect(on_canceled)
        recogniser.session_stopped.connect(on_session_stopped)

        t0 = time.time()
        recogniser.start_continuous_recognition_async().get()
        done.wait()
        recogniser.stop_continuous_recognition_async().get()
        t1 = time.time()

        if error_info["canceled"]:
            logger.error(f"Azure Speech recognition failed: {error_info['details']}")

        full_text = " ".join(parts).strip()
        
        if not full_text:
            logger.error(f"Azure Speech produced no transcription for {wav_path}")

        debug = {
            "mode": "continuous",
            "recognized_segments": len(parts),
            "final_text_len_chars": len(full_text),
        }

        return full_text, (t1 - t0), debug
