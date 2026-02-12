DEFAULT_VOICES = [
    # "JBFqnCBsd6RMkjVDRZzb",
    # "EXAVITQu4vr4xnSDxMaL",
    "snf0TZa0mc0w5XJsWQBI",  # created social worker 
    "21m00Tcm4TlvDq8ikWAM",   # narrator
    # "AZnzlk1XvdvUeBnXmlld",    storyteller
]

PYTHONHASHSEED=0 

def get_voice_for_speaker(speaker: str, fallback_pool=DEFAULT_VOICES) -> str:
    # if speaker in voice_map:
    #     return voice_map[speaker]
    # assign a fallback voice deterministically
    return fallback_pool[hash(speaker) % len(fallback_pool)]
