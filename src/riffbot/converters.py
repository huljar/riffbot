import re
import typing

_position_regex = re.compile("^(?P<hm>\\d\\d?)(:(?P<m>\\d\\d))?(:(?P<s>\\d\\d))$")


def to_position(arg) -> typing.Optional[typing.Tuple[int, int, int]]:
    match = _position_regex.match(arg)
    if match:
        h, m, s = match.group("hm", "m", "s")
        if m is None:
            m = h
            h = "0"
        return (int(h), int(m), int(s))
    return None
