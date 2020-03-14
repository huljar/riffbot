import math


def to_human_readable_position(seconds: int) -> str:
    h = math.floor(seconds / 3600)
    m = math.floor((seconds % 3600) / 60)
    s = seconds % 60
    return f"{f'{h}:' if h > 0 else ''}{f'{m:02d}' if h > 0 else m}:{s:02d}"
