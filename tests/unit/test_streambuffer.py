import io
import unittest
from audio import streambuffer as sb


class TestStreamBuffer(unittest.TestCase):
    def setUp(self):
        self.sb = sb.StreamBuffer(slot_size=32, slot_count=5)  # small buffer

    def test_slot_write_read1(self):
        written_bytes = b"Exactly one slot worth of bytes!"
        self.sb.write(written_bytes)
        self.assertEqual(self.sb._distance(), 1)
        read_bytes = self.sb.read1()
        self.assertEqual(read_bytes, written_bytes)
        self.assertEqual(self.sb._distance(), 0)

        written_bytes = (b"A bit more than a single slot! A"
                         b"bout 1.5 slots...")
        self.sb.write(written_bytes)
        self.assertEqual(self.sb._distance(), 2)
        read_bytes = self.sb.read()
        self.assertEqual(read_bytes, written_bytes[:32])
        self.assertEqual(self.sb._distance(), 1)
        read_bytes = self.sb.read1()
        self.assertEqual(read_bytes, written_bytes[32:])
        self.assertEqual(self.sb._distance(), 0)

        with self.assertRaises(io.BlockingIOError):
            read_bytes = self.sb.read1()

    def test_multi_slot_write_read(self):
        written_bytes = (b"This byte sequence is a bit long"
                         b"er. It contains more than 3 slot"
                         b"s worth of data actually! That's"
                         b" almost 4 slots!")
        self.sb.write(written_bytes)
        read_bytes = self.sb.read(40)
        self.assertEqual(read_bytes, written_bytes[:40])
        self.assertEqual(self.sb._distance(), 2)

        read_bytes = self.sb.read1(10)
        self.assertEqual(read_bytes, written_bytes[40:50])
        self.assertEqual(self.sb._distance(), 2)  # only read cache was touched, so same distance

        read_bytes = self.sb.read(25)
        self.assertEqual(read_bytes, written_bytes[50:75])
        self.assertEqual(self.sb._distance(), 1)

        with self.assertRaises(io.BlockingIOError):
            read_bytes = self.sb.read(54)  # attempt to read 1 byte too much

        read_bytes = self.sb.read(53)
        self.assertEqual(len(read_bytes), 37)  # last slot was not full, so less bytes are returned
        self.assertEqual(read_bytes, written_bytes[75:])
        self.assertEqual(self.sb._distance(), 0)
