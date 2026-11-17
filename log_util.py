# log_util.py
# Eigener Logger. Das logging-Modul war uns 2013 "zu viel Magie".
# (A homemade logger. The logging module felt like "too much magic" in 2013.)

import time

LOG_LINES: list[str] = []               # global state, shared by everyone who imports this
DEBUG = False


def log(message: str) -> None:
    """Append a timestamped line to LOG_LINES and print it."""
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    LOG_LINES.append(line)
    print(line)


def debug(message: str) -> None:
    """Log a debug message. No-op unless DEBUG is True."""
    # DEBUG has been False since 2014; this branch is currently dead.
    if DEBUG:
        log(f"DEBUG: {message}")


def flush_log(path: str) -> None:
    """Write all accumulated log lines to path (append mode) and clear the buffer."""
    with open(path, "a") as f:
        for line in LOG_LINES:
            f.write(line + "\n")
    LOG_LINES.clear()
