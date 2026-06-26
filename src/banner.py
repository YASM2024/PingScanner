import sys

APP_NAME = "PingScanner"
VERSION = "V1.1"
AUTHOR = "Miyazaki Yasuo"
RELEASE_DATE = "2026-06-26"
BANNER_LINE = "=" * 61


def print_banner():
    print(BANNER_LINE)
    print(f"{APP_NAME} {VERSION}")
    print(f"Created by {AUTHOR}")
    print(f"Released on {RELEASE_DATE}")
    print(BANNER_LINE)
    print()


def pause_console():
    if sys.stdin.isatty():
        try:
            input("Press Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass
