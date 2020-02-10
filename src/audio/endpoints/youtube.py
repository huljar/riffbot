import pafy
import requests
from typing import Generator

from audio.endpoint import Endpoint


class YouTubeEndpoint(Endpoint):
    def __init__(self, url: str):
        self._video = pafy.new(url)

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        stream = self._video.getbestaudio(preftype="m4a")
        url = stream.url_https
        print(stream)
        print(url)
        file_size = stream.get_filesize()
        with requests.Session() as session:
            for i in range(0, file_size, chunk_size):
                chunk_url = url + f"&range={i}-{min(i+chunk_size-1, file_size-1)}"
                response = session.get(chunk_url)
                print("Yielding chunk")
                yield response.content

    def get_chunk_size(self) -> int:
        return 131072  # 128 KB

    def get_song_description(self) -> str:
        return self._video.title
