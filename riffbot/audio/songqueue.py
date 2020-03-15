import collections
import logging
import random
from typing import List, Optional, Union

from riffbot.endpoints.endpoint import Endpoint
from riffbot.utils import utils

_logger = logging.getLogger(__name__)


class InvalidPositionError(Exception):
    pass


class SongQueue:
    def __init__(self):
        _logger.debug("Initializing")
        self._queue = collections.deque()

    def __del__(self):
        _logger.debug("Destroying")

    def enqueue(self, endpoints: Union[Endpoint, List[Endpoint]], *, pos: Optional[int] = None):
        if isinstance(endpoints, Endpoint):
            endpoints = [endpoints]
        _logger.debug(f"Enqueueing {len(endpoints)} songs{f' at pos {pos}' if pos is not None else ''}")
        if pos is not None:
            if pos < 0 or pos > self.size():
                raise InvalidPositionError(f"Position {pos} is out of bounds (queue size: {self.size()})")
            for offset, endpoint in enumerate(endpoints):
                self._queue.insert(pos + offset, endpoint)
        else:
            self._queue.extend(endpoints)

    def shuffle(self) -> None:
        _logger.debug("Shuffling the queue")
        elements = self.list()
        random.shuffle(elements)
        self.clear()
        self._queue.extend(elements)

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

    def get_total_length(self) -> int:
        return utils.get_total_length(self._queue)
