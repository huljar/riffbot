from blinker import signal
from .endpoint import Endpoint
from .streambuffer import StreamBuffer, DEPLETION_SIGNAL_NAME

SLOT_SIZE = 128 * 1024  # 128 KB
SLOT_COUNT = 8  # 1 MB total buffer size
DEPLETION_THRESHOLD = 4  # 512 KB depletion warning threshold


class Player:
    def __init__(self, endpoint: Endpoint, *, init_chunks: int):
        self._endpoint = endpoint
        self._buffer = StreamBuffer(slot_size=SLOT_SIZE, slot_count=SLOT_COUNT,
                                    depletion_threshold=DEPLETION_THRESHOLD)
        self._loading = False

        # Load inital chunks into buffer
        self._chunk_generator = self._endpoint.stream_chunks(SLOT_SIZE)
        try:
            for i in range(init_chunks):
                self._buffer.write(next(self._chunk_generator))
        except StopIteration:
            self._buffer.seal()

        # Connect depletion signal
        signal(DEPLETION_SIGNAL_NAME).connect(self._on_depletion_warning, sender=self._buffer)

    def _on_depletion_warning(self, sender):
        if sender is not self._buffer:
            raise f"Unexpected depletion signal from {sender}, this should never happen"

        if not self._loading:
            self._loading = True
            try:
                while(self._buffer.distance() <= DEPLETION_THRESHOLD):
                    self._buffer.write(next(self._chunk_generator))
            except StopIteration:
                self._buffer.seal()
                signal(DEPLETION_SIGNAL_NAME).disconnect(self._on_depletion_warning, sender=self._buffer)
            finally:
                self._loading = False
