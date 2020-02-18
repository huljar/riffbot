import pafy
import requests
from typing import Generator
import re

from ..endpoint import Endpoint, InvalidEndpointError


_range_variants = {
    "&range={}-{}": re.compile("^https://.*\\.googlevideo\\.com/videoplayback\\?([^/]+=[^/]*&)*[^/]+=[^/]*$"),
    "range/{}-{}/": re.compile("^https://.*\\.googlevideo\\.com/videoplayback/([^&=?]+/)+$")
}


class YouTubeEndpoint(Endpoint):
    def __init__(self, url: str):
        self._video = pafy.new(url)
        self._stream = self._video.getbestaudio(preftype="m4a")

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        url = self._stream.url_https
        template = self._get_url_variant(url)
        file_size = self._stream.get_filesize()
        with requests.Session() as session:
            for i in range(0, file_size, chunk_size):
                chunk_url = url + template.format(i, min(i+chunk_size-1, file_size-1))
                response = session.get(chunk_url)
                yield response.content

    def get_preferred_chunk_size(self) -> int:
        return 65536  # 64 KB

    def get_song_description(self) -> str:
        return self._video.title

    def get_bit_rate(self) -> int:
        return self._stream.rawbitrate

    def get_length(self) -> int:
        return self._video.length

    def _get_url_variant(self, url: str) -> str:
        for template, regex in _range_variants.items():
            if regex.match(url) is not None:
                return template
        raise InvalidEndpointError()
