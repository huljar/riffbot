import queue

from audio.player import Player


class NotConnectedError(Exception):
    pass


class SongQueue:
    def __init__(self, song_over):
        self._queue = queue.Queue()
        self._player = None
        self._notify_song_over = song_over

    def __del__(self):
        if self._player is not None:
            self._player.stop()

    def set_voice_client(self, voice_client):
        self._voice_client = voice_client

    def enqueue(self, endpoint):
        if self._voice_client is None:
            raise NotConnectedError()

        self._queue.put_nowait(endpoint)
        if self._player is None:
            self._play_next()
        return self._queue.qsize()

    def get_player(self):
        return self._player

    def _on_song_finished(self, error):
        self._player = None
        if self._notify_song_over:
            self._notify_song_over(self._queue.qsize())
        if not self._queue.empty():
            self._play_next()

    def _play_next(self):
        endpoint = self._queue.get_nowait()
        self._player = Player(endpoint, self._voice_client, self._on_song_finished)
