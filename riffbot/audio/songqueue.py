import collections
import logging
from typing import List, Optional, Union

from riffbot.endpoints.endpoint import Endpoint

_logger = logging.getLogger(__name__)


class SongQueue:
    def __init__(self):
        _logger.debug("Initializing")
        self._queue = collections.deque()

    def __del__(self):
        _logger.debug("Destroying")

    def enqueue(self, endpoints: Union[Endpoint, List[Endpoint]]):
        if isinstance(endpoints, Endpoint):
            endpoints = [endpoints]
        _logger.debug(f"Enqueueing {len(endpoints)} songs")
        self._queue.extend(endpoints)

    def get_next(self) -> Optional[Endpoint]:
        try:
            return self._queue.popleft()
        except IndexError:
            return None

    def list(self) -> List[Endpoint]:
        return [endpoint for endpoint in self._queue]

    def clear(self):
        self._queue.clear()

    def size(self) -> int:
        return len(self._queue)
