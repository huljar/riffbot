import functools
import math
from typing import Iterable

from riffbot.endpoints.endpoint import Endpoint

_digits = {"0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
           "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"}


def to_human_readable_position(seconds: int) -> str:
    h = math.floor(seconds / 3600)
    m = math.floor((seconds % 3600) / 60)
    s = seconds % 60
    return f"{f'{h}:' if h > 0 else ''}{f'{m:02d}' if h > 0 else m}:{s:02d}"


def to_keycap_emojis(num: int) -> str:
    return "".join([_digits[d] for d in (str(num))])


def get_total_length(endpoints: Iterable[Endpoint]) -> int:
    return functools.reduce(lambda acc, val: acc + val, [e.get_length() for e in endpoints], 0)
