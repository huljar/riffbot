import pafy

from audio.endpoint import Endpoint

class YouTubeEndpoint(Endpoint):
    def init_stream(self, url):
        video = pafy.new(url)
        print(f"Downloading {video.title} …")
        self.stream = video.getbestaudio(preftype="m4a")
        for s in video.audiostreams:
            print(s.bitrate, s.extension, s.get_filesize())
        print(f"I chose ({self.stream.bitrate} {self.stream.extension} {self.stream.get_filesize()})")
        # self.buffer = self.stream.stream_to_buffer()
        print(f"The stream URL is")
        self.stream.download("test.m4a")
        print("Download finished!")
