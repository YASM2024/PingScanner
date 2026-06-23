import subprocess
from concurrent.futures import (
    FIRST_COMPLETED,
    ThreadPoolExecutor,
    wait,
)
from datetime import datetime

from rate_limiter import RateLimiter
from scan_control import ScanAborted, StopController


class PingScanner:

    def __init__(
        self,
        timeout_ms=1000,
        parallel=4,
        ping_interval_ms=200,
        stop_controller=None,
    ):

        self.timeout_ms = timeout_ms
        self.parallel = parallel
        self._rate_limiter = RateLimiter(
            ping_interval_ms
        )
        self._stop = (
            stop_controller
            or StopController()
        )

    def request_stop(self):

        self._stop.request_stop()

    def ping(self, ip):

        self._stop.check_stop()

        self._rate_limiter.wait()

        self._stop.check_stop()

        sent_at = datetime.now()

        cmd = [
            "ping",
            "-n", "1",
            "-w", str(self.timeout_ms),
            ip,
        ]

        try:

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=(
                    self.timeout_ms / 1000
                ) + 2,
            )

            stdout = result.stdout.lower()

            success = (
                "ttl=" in stdout
            )

            if success:
                checked_at = datetime.now()
            else:
                checked_at = sent_at

            return ip, success, checked_at

        except Exception:

            return ip, False, sent_at

    def scan_iter(self, ip_list):

        if not ip_list:
            return

        with ThreadPoolExecutor(
            max_workers=self.parallel
        ) as executor:

            pending = set()
            ip_iter = iter(ip_list)

            for _ in range(
                min(
                    self.parallel,
                    len(ip_list),
                )
            ):
                self._stop.check_stop()
                pending.add(
                    executor.submit(
                        self.ping,
                        next(ip_iter),
                    )
                )

            while pending:

                done, pending = wait(
                    pending,
                    return_when=(
                        FIRST_COMPLETED
                    ),
                )

                for future in done:

                    yield future.result()

                    if self._stop.is_stop_requested():
                        for pending_future in pending:
                            pending_future.cancel()
                        pending.clear()
                        raise ScanAborted()

                    try:
                        self._stop.check_stop()
                        pending.add(
                            executor.submit(
                                self.ping,
                                next(ip_iter),
                            )
                        )
                    except StopIteration:
                        pass

    def scan(self, ip_list):

        return list(
            self.scan_iter(ip_list)
        )
