import functools
import math
from typing import Iterable, Optional, Union

from i18n import t

from riffbot.endpoints.endpoint import Endpoint

_digits = {"0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
           "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"}


def to_human_readable_position(length: Optional[Union[int, float]], locale: str) -> str:
    if length is None:
        return t("misc.unknown_length_placeholder", locale=locale)
    length = int(round(length))
    h = math.floor(length / 3600)
    m = math.floor((length % 3600) / 60)
    s = length % 60
    return f"{f'{h}:' if h > 0 else ''}{f'{m:02d}' if h > 0 else m}:{s:02d}"


def to_keycap_emojis(num: int) -> str:
    return "".join([_digits[d] for d in (str(num))])


def get_total_length(endpoints: Iterable[Endpoint]) -> int:
    return functools.reduce(
        lambda acc, val: acc + val, [e.get_length() if e.get_length() is not None else 0 for e in endpoints], 0)
