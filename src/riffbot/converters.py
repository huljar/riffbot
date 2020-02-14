import re
import typing

from youtube_search import YoutubeSearch

_youtube_regex = re.compile(
    "^(https?://)?((www\\.)?youtube\\.com/watch\\?v=|youtu\\.be/)(?P<id>[\\w\\-]{11})([?&]\\S+)?$")
_position_regex = re.compile("^(?P<hm>\\d\\d?)(:(?P<m>\\d\\d))?(:(?P<s>\\d\\d))$")


def to_youtube_video(args) -> typing.Optional[str]:
    if len(args) == 0:
        return None
    if len(args) == 1:
        match = _youtube_regex.match(args[0])
        if match:
            return match.group("id")
    search_results = YoutubeSearch(" ".join(args), max_results=1).to_dict()
    if len(search_results) > 0:
        return search_results[0]["id"]
    return None


def to_position(arg) -> typing.Optional[typing.Tuple[int, int, int]]:
    match = _position_regex.match(arg)
    if match:
        h, m, s = match.group("hm", "m", "s")
        if m is None:
            m = h
            h = "0"
        return (int(h), int(m), int(s))
    return None
