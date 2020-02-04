import os
import unittest
from audio import player
from audio.endpoints import youtube as yt


class TestPlayer(unittest.TestCase):
    def setUp(self):
        endpoint = yt.YouTubeEndpoint("https://www.youtube.com/watch?v=pm105KodBsg")
        self.player = player.Player(endpoint, init_chunks=5)

    def test_initial_chunks(self):
        with open(os.path.dirname(os.path.abspath(__file__)) + "/data/song1.m4a", "rb") as file:
            verification = file.read(5*player.SLOT_SIZE)
            for i in range(5):
                self.assertEqual(self.player._buffer.read1(), verification[i*player.SLOT_SIZE:(i+1)*player.SLOT_SIZE])
