DEFAULT_VOICES = [
    # "JBFqnCBsd6RMkjVDRZzb",
    # "EXAVITQu4vr4xnSDxMaL",
    # "AZnzlk1XvdvUeBnXmlld",    storyteller
    # "snf0TZa0mc0w5XJsWQBI",  # Social care worker
    "qimfC2HPDJhhTmdOzs2z",  # Eastern European man
    "hhDdiMwM9dWfw6qEFzju",  # Young Mancunian
]

"""
A social care worker from the South East of England. 
Formal but not overly so, works with vulnerable people (homelessness, job security, children)
Should be confident, assuring & sound natural

"""
PYTHONHASHSEED = 0


def get_voice_for_speaker(speaker: str, fallback_pool=DEFAULT_VOICES) -> str:
    # if speaker in voice_map:
    #     return voice_map[speaker]
    # assign a fallback voice deterministically
    return fallback_pool[hash(speaker) % len(fallback_pool)]
