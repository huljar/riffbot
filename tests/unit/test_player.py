import unittest
from unittest.mock import MagicMock

from audio import player
from audio.endpoints import youtube as yt


class TestPlayer(unittest.TestCase):
    def setUp(self):
        endpoint = yt.YouTubeEndpoint("https://www.youtube.com/watch?v=pm105KodBsg")
        voice_client = MagicMock()
        self.player = player.Player(endpoint, voice_client)
