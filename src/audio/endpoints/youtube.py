import pafy
import requests
from typing import Generator

from audio.endpoint import Endpoint


class YouTubeEndpoint(Endpoint):
    def __init__(self, url: str):
        video = pafy.new(url)
        print(f"Title: {video.title}")
        stream = video.getbestaudio(preftype="m4a")
        for s in video.audiostreams:
            print(s.bitrate, s.extension, s.get_filesize())
        print(
            f"I chose ({stream.bitrate} {stream.extension} {stream.get_filesize()})")
        # self.buffer = self.stream.stream_to_buffer()
        print(f"The stream URL is {stream.url_https}")
        self.stream_url = stream.url_https
        self.stream_size = stream.get_filesize()

    def stream_chunks(self, chunk_size: int) -> Generator[bytes, None, None]:
        with requests.get(self.stream_url, stream=True) as request:
            yield from request.iter_content(chunk_size)
