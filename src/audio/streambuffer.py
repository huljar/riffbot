import io
import math
from deps import ringbuffer as rb

SLOT_SIZE = 32 * 1024  # 32 KB
SLOT_COUNT = 32  # 1 MB total buffer size


class StreamBuffer(io.BufferedIOBase):
    def __init__(self):
        self._rb = rb.RingBuffer(slot_bytes=SLOT_SIZE, slot_count=SLOT_COUNT)
        self._reader = self._rb.new_reader()
        self._rb.new_writer()
        self._writer = self._rb.writer

        self._read_cache = bytearray()
        self._sealed = False

    def detach(self):
        raise io.UnsupportedOperation()

    def read(self, size=-1):
        bytes_to_read = (SLOT_SIZE if size is None or size < 0 else size) - len(self._read_cache)
        slots_to_read = 0 if bytes_to_read <= 0 else math.ceil(bytes_to_read / SLOT_SIZE)

        if self._reader.get().counter + slots_to_read > self._writer.get().counter:
            raise io.BlockingIOError()

        try:
            return self._rb.try_read(self._reader)
        except (rb.WriterFinishedError, rb.WaitingForWriterError):
            raise io.BlockingIOError()

    def read1(self, size=-1):
        return self.read(SLOT_SIZE if size == -1 else size)

    def readinto(self, b):
        b[0:SLOT_SIZE] = self.read1()
        return SLOT_SIZE

    def readinto1(self, b):
        return self.readinto(b)

    def write(self, b):
        slots_to_write = math.ceil(len(b) / SLOT_SIZE)
        writable_slots = SLOT_COUNT - self._distance()

        if slots_to_write > writable_slots:
            raise io.BlockingIOError()

        try:
            for i in range(0, len(b), SLOT_SIZE):
                self._rb.try_write(b[i:i+SLOT_SIZE])
        except rb.WaitingForReaderError:
            raise io.BlockingIOError()

    def seal(self):
        """ Indicate that the stream is fully downloaded and no more data will be written to the buffer."""
        self._sealed = True

    def _distance(self):
        """ Returns the distance that the writer is ahead of the reader """
        dist = self._writer.get().counter - self._reader.get().counter
        if dist > SLOT_COUNT:
            raise f"distance {dist} is greater than SLOT_COUNT {SLOT_COUNT}, this should never happen"
        return dist
