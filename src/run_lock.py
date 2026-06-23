import atexit
import os
import sys
from pathlib import Path


class RunLockError(Exception):
    pass


class RunLock:

    def __init__(self, lock_path):

        self.lock_path = Path(lock_path)
        self._acquired = False

    def _is_process_running(self, pid):

        if pid <= 0:
            return False

        if sys.platform == "win32":

            import ctypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                pid,
            )

            if handle:
                kernel32.CloseHandle(handle)
                return True

            return False

        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def acquire(self):

        if self.lock_path.exists():

            try:
                pid = int(
                    self.lock_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )
            except (ValueError, OSError):
                pid = -1

            if self._is_process_running(pid):
                raise RunLockError(
                    "Another instance is already "
                    f"running (PID {pid}). "
                    f"Lock: {self.lock_path}"
                )

            self.lock_path.unlink(
                missing_ok=True
            )

        self.lock_path.write_text(
            str(os.getpid()),
            encoding="utf-8",
        )

        self._acquired = True
        atexit.register(self.release)

    def release(self):

        if not self._acquired:
            return

        try:

            if self.lock_path.exists():

                content = (
                    self.lock_path.read_text(
                        encoding="utf-8"
                    ).strip()
                )

                if content == str(os.getpid()):
                    self.lock_path.unlink()

        except OSError:
            pass

        self._acquired = False

    def __enter__(self):

        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):

        self.release()
        return False
