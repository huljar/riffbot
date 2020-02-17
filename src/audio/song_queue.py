import collections
import logging
import typing

from audio.endpoint import Endpoint
from audio.player import Player

_logger = logging.getLogger("riffbot." + __name__)


class NotConnectedError(Exception):
    pass


class SongQueue:
    def __init__(self, song_over: typing.Callable[[], typing.Awaitable[None]]):
        _logger.debug(f"Initializing with song_over={song_over}")
        self._queue = collections.deque()
        self._player = None
        self._notify_song_over = song_over

    def __del__(self):
        _logger.debug("Destroying")
        self.skip()

    def set_voice_client(self, voice_client):
        self._voice_client = voice_client

    def enqueue(self, endpoint: Endpoint):
        _logger.debug(f"Enqueueing \"{endpoint.get_song_description()}\"")
        if self._voice_client is None:
            raise NotConnectedError()

        self._queue.append(endpoint)
        if self._player is None:
            self._play_next()
        return len(self._queue)

    def skip(self):
        _logger.debug("Skipping")
        if self._player:
            self._player.stop()

    def get_current(self) -> typing.Optional[Endpoint]:
        return self._player.get_endpoint() if self._player else None

    def get_next(self) -> typing.Optional[Endpoint]:
        if len(self._queue) == 0:
            return None
        return self._queue[0]

    def get_enqueued(self) -> typing.List[Endpoint]:
        return [endpoint for endpoint in self._queue]

    def get_all(self) -> typing.List[Endpoint]:
        ret = [self._player.get_endpoint()] if self._player else []
        ret.extend(self.get_enqueued())
        return ret

    def size(self) -> int:
        return len(self._queue)

    def get_player(self):
        return self._player

    async def _on_song_finished(self, error):
        _logger.debug(f"Song finished playing")
        if error is not None:
            _logger.error(f"Error occurred during song: {error}")
        self._player = None
        if self._notify_song_over:
            await self._notify_song_over()
        if len(self._queue) > 0:
            self._play_next()

    def _play_next(self):
        _logger.debug("Playing next song")
        endpoint = self._queue.popleft()
        self._player = Player(endpoint, self._voice_client, self._on_song_finished)
