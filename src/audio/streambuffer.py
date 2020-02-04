from blinker import signal
import io
import math
from deps import ringbuffer as rb

DEPLETION_SIGNAL_NAME = "StreamBufferAlmostDepleted"


class StreamBuffer(io.BufferedIOBase):
    def __init__(self, *, slot_size: int, slot_count: int, depletion_threshold: int):
        self._rb = rb.RingBuffer(slot_bytes=slot_size, slot_count=slot_count)
        self._slot_size = slot_size
        self._slot_count = slot_count
        self._reader = self._rb.new_reader()
        self._rb.new_writer()
        self._writer = self._rb.writer
        self._read_cache = bytearray()
        self._depletion_threshold = depletion_threshold
        self._sealed = False

    def seal(self):
        """ Indicate that the stream is fully downloaded and no more data will be written to the buffer."""
        self._sealed = True
        self._rb.writer_done()

    def distance(self):
        """ Returns the distance that the writer is ahead of the reader """
        dist = self._writer.get().counter - self._reader.get().counter
        if dist > self._slot_count:
            print(f"distance {dist} is greater than self._slot_count {self._slot_count}, this should never happen")
            raise io.UnsupportedOperation()
        return dist

    ############################################################
    # The following methods represent the BufferedIO interface #
    ############################################################
    def detach(self):
        raise io.UnsupportedOperation()

    def read(self, size=-1):
        if self._sealed and self.distance() == 0 and len(self._read_cache) == 0:
            return bytes()

        return_bytes = self._slot_size if size is None or size < 0 else size
        cached_bytes = len(self._read_cache)
        bytes_to_read = max(0, return_bytes - cached_bytes)
        slots_to_read = 0 if bytes_to_read <= 0 else math.ceil(bytes_to_read / self._slot_size)

        if self._reader.get().counter + slots_to_read > self._writer.get().counter:
            raise io.BlockingIOError()

        # Use the cached bytes
        builder = bytearray()
        builder += self._read_cache[:return_bytes]
        del self._read_cache[:return_bytes]

        # Read more bytes (if necessary)
        try:
            for remaining_bytes in range(bytes_to_read, 0, -self._slot_size):
                read_bytes = self._rb.try_read(self._reader)
                builder += read_bytes[:remaining_bytes]
                self._read_cache = read_bytes[remaining_bytes:]
        except rb.WaitingForWriterError:
            print("ran into a pre-checked error, this should never happen")
            raise io.BlockingIOError()
        except rb.WriterFinishedError:
            pass

        # Emit depletion warning if necessary
        if not self._sealed and self.distance() <= self._depletion_threshold:
            signal(DEPLETION_SIGNAL_NAME).send(self)

        return bytes(builder)

    def read1(self, size=-1):
        return self.read(self._slot_size if size == -1 else min(size, self._slot_size))

    def readinto(self, b):
        b[:self._slot_size] = self.read1()
        return self._slot_size

    def readinto1(self, b):
        return self.readinto(b)

    def write(self, b):
        """ Write bytes-like data into the buffer.

        Note that len(b) must be a multiple of self._slot_size unless it is the last chunk that is written to the buffer
        (and seal() will be called afterwards).
        """
        if self._sealed:
            raise io.BlockingIOError()

        slots_to_write = math.ceil(len(b) / self._slot_size)
        writable_slots = self._slot_count - self.distance()

        if slots_to_write > writable_slots:
            raise io.BlockingIOError()

        try:
            for i in range(0, len(b), self._slot_size):
                self._rb.try_write(b[i:i+self._slot_size])
        except rb.WaitingForReaderError:
            raise io.BlockingIOError()
