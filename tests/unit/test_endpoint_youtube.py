import os
import unittest

from audio.endpoints import youtube as yt
from audio.player import CHUNK_SIZE


class TestYoutubeEndpoint(unittest.TestCase):
    def test_song1(self):
        endpoint = yt.YouTubeEndpoint("https://www.youtube.com/watch?v=pm105KodBsg")
        download = b"".join([chunk for chunk in endpoint.stream_chunks(CHUNK_SIZE)])
        with open(os.path.dirname(os.path.abspath(__file__)) + "/data/song1.m4a", "rb") as file:
            verification = file.read()
            self.assertEqual(download, verification)
