import pafy
import requests

from audio.endpoint import Endpoint
from audio.streambuffer import SLOT_SIZE


class YouTubeEndpoint(Endpoint):
    def __init__(self, url):
        video = pafy.new(self.url)
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

    def get_chunk(self):
        with requests.get(self.stream_url, stream=True) as request:
            yield from request.iter_content(SLOT_SIZE)
