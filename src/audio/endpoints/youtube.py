import pafy
import requests
from typing import Generator

from audio.endpoint import Endpoint


class YouTubeEndpoint(Endpoint):
    def __init__(self, url: str):
        video = pafy.new(url)
        stream = video.getbestaudio(preftype="m4a")
        self.stream_url = stream.url_https
        self.stream_size = stream.get_filesize()

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        with requests.get(self.stream_url, stream=True) as request:
            yield from request.iter_content(chunk_size)
