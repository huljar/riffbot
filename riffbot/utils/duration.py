import time


class Duration:
    def __init__(self):
        self.reset()

    def reset(self):
        self._seconds_until_pause = 0.0
        self._running = False

    def start(self):
        self._start_time = time.time()
        self._running = True

    def pause(self):
        pause_time = time.time()
        self._seconds_until_pause += pause_time - self._start_time
        self._running = False

    def get(self) -> float:
        present_time = time.time()
        seconds = self._seconds_until_pause
        if self._running:
            seconds += present_time - self._start_time
        return seconds
