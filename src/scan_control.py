import signal
from pathlib import Path


class ScanAborted(Exception):
    pass


class StopController:

    def __init__(self, stop_file=None):

        self._stop_requested = False
        self.stop_file = (
            Path(stop_file)
            if stop_file
            else None
        )

    def request_stop(self):

        self._stop_requested = True

    def is_stop_requested(self):

        if self._stop_requested:
            return True

        if (
            self.stop_file
            and self.stop_file.exists()
        ):
            self._stop_requested = True
            return True

        return False

    def check_stop(self):

        if self.is_stop_requested():
            raise ScanAborted()

    def consume_stop_file(self):

        if (
            self.stop_file
            and self.stop_file.exists()
        ):
            self.stop_file.unlink(
                missing_ok=True
            )

    def install_signal_handler(self):

        def _handler(signum, frame):

            self.request_stop()

        signal.signal(
            signal.SIGINT,
            _handler,
        )

        if hasattr(signal, "SIGTERM"):
            signal.signal(
                signal.SIGTERM,
                _handler,
            )
