import re
from typing import List, Optional, Tuple, Union

import pafy
from youtube_search import YoutubeSearch

_youtube_video_regex = re.compile(
    "^(https?://)?((www\\.)?youtube\\.com/watch\\?v=|youtu\\.be/)(?P<id>[\\w\\-]{11})([?&]\\S+)?$")
_youtube_playlist_regex = re.compile(
    "^(https?://)?(www\\.)?youtube\\.com/(watch\\?v=([\\w\\-]{11})&|playlist\\?)list="
    "(?P<list>(PL|RD)[\\w\\-]{11,43})([?&]\\S+)?$")
_position_regex = re.compile("^(?P<hm>\\d\\d?)(:(?P<m>\\d\\d))?(:(?P<s>\\d\\d))$")


def to_youtube_videos(args: List[str]) -> Optional[List[Union[str, pafy.pafy.Pafy]]]:
    if len(args) == 0:
        return None
    if len(args) == 1:
        # First try playlist match
        match = _youtube_playlist_regex.match(args[0])
        if match:
            playlist = pafy.get_playlist(match.group("list"))
            return list(map(lambda entry: entry["pafy"], playlist["items"]))

        # If it's not a playlist, try single video
        match = _youtube_video_regex.match(args[0])
        if match:
            return [match.group("id")]

    # Multiple arguments, use as search input
    search_results = YoutubeSearch(" ".join(args), max_results=1).to_dict()
    if len(search_results) > 0:
        return [search_results[0]["id"]]
    return None


def to_position(arg: str) -> Optional[Tuple[int, int, int]]:
    match = _position_regex.match(arg)
    if match:
        h, m, s = match.group("hm", "m", "s")
        if m is None:
            m = h
            h = "0"
        return (int(h), int(m), int(s))
    return None
