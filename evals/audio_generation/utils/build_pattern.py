import re

def build_pattern(speakers: list[str]) -> str:
    escaped = [re.escape(s) for s in speakers]
    group = "|".join(escaped)
    return rf"({group}):\s*(.+?)(?=({group}):|$)"
