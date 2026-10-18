"""Prints log lines, and keeps the newest ones until they upload to Memfault."""

DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3

CAPACITY = 100

_lines: list = []


def log(text: str, level: int = INFO) -> None:
    """Print a line and keep it for upload."""
    print(text)
    _lines.append((level, text))
    if len(_lines) > CAPACITY:
        del _lines[0]


def kept_lines() -> list:
    """Return the kept (level, text) pairs, oldest first."""
    return list(_lines)


def discard_lines(count: int) -> None:
    """Forget the oldest count lines."""
    del _lines[:count]
