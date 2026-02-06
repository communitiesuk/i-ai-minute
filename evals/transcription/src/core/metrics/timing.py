class TimingAccumulator:
    def __init__(self):
        self.process_sec = 0.0
        self.audio_sec = 0.0

    def add(self, audio_sec: float, process_sec: float):
        self.audio_sec += float(audio_sec)
        self.process_sec += float(process_sec)

    @property
    def rtf(self) -> float:
        return self.process_sec / self.audio_sec if self.audio_sec else float("nan")
