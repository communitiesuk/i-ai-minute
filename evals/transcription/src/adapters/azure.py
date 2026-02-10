from common.services.transcription_services.azure import AzureSpeechAdapter as CommonAzureAdapter

from evals.transcription.src.adapters.base import ServiceTranscriptionAdapter


def AzureSTTAdapter() -> ServiceTranscriptionAdapter:
    return ServiceTranscriptionAdapter(CommonAzureAdapter, "Azure Speech API")
