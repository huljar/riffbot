import asyncio
import collections
import logging
import typing

from riffbot.endpoints.endpoint import Endpoint
from .player import Player

_logger = logging.getLogger(__name__)


class NotConnectedError(Exception):
    pass


class SongQueue:
    def __init__(self):
        _logger.debug("Initializing")
        self._queue = collections.deque()
        self._player = None
        self._song_over_handlers = []

    def __del__(self):
        _logger.debug("Destroying")
        self.skip()

    def attach_song_over(self, handler: typing.Callable[[], typing.Awaitable[None]]):
        _logger.debug("Attaching song over handler")
        self._song_over_handlers.append(handler)

    def detach_song_over(self, handler: typing.Callable[[], typing.Awaitable[None]]):
        _logger.debug("Detaching song over handler")
        try:
            self._song_over_handlers.remove(handler)
        except ValueError:
            _logger.debug("Detach failed, handler is not attached")

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
        await asyncio.gather(*[handler() for handler in self._song_over_handlers])
        if len(self._queue) > 0:
            self._play_next()

    def _play_next(self):
        _logger.debug("Playing next song")
        endpoint = self._queue.popleft()
        self._player = Player(endpoint, self._voice_client, self._on_song_finished)
