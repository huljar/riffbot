import pafy
import requests
from typing import Generator

from audio.endpoint import Endpoint


class YouTubeEndpoint(Endpoint):
    def __init__(self, url: str):
        self._video = pafy.new(url)

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        stream = self._video.getbestaudio(preftype="m4a")
        session = requests.Session()
        with session.get(stream.url_https, stream=True) as request:
            yield from request.iter_content(chunk_size)

    def get_song_description(self) -> str:
        return self._video.title
