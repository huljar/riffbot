from endpoint import Endpoint
from streambuffer import StreamBuffer


class Player:
    def __init__(self, endpoint: Endpoint):
        self._endpoint = endpoint
        self._buffer = StreamBuffer()
