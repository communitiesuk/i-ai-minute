from __future__ import annotations


class FakeAdapter:
    def __init__(self, label: str, hyp: str, proc_sec: float = 0.25):
        self.name = label
        self.label = label
        self.hyp = hyp
        self.proc_sec = proc_sec

    def transcribe(self, wav_path: str):  # noqa: ARG002
        return {"text": self.hyp, "duration_sec": self.proc_sec, "debug_info": {"label": self.label}}


class FakeDataset:
    def __init__(self, samples: list[dict]):
        self._samples = samples

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int) -> dict:
        return self._samples[idx]
