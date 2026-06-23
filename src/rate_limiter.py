import threading
import time


class RateLimiter:

    def __init__(self, interval_ms):

        self._interval = interval_ms / 1000.0
        self._lock = threading.Lock()
        self._next_allowed = 0.0

    def wait(self):

        with self._lock:

            now = time.monotonic()

            if now < self._next_allowed:
                time.sleep(
                    self._next_allowed - now
                )

            self._next_allowed = (
                time.monotonic()
                + self._interval
            )
