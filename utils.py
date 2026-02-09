"""Utility Functions for Inventory System

Provides helper functions used throughout the application.
"""

from datetime import datetime


def timestamp():
    """Get current timestamp as formatted string.

    Returns:
        str: Timestamp in format YYYY-MM-DD HH:MM
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def read_log_tail_reverse(path, lines=100):
    """Return the last `lines` lines from a log file in newest-first order.

    This is a convenience helper for viewing logs with the most recent
    entries at the top (useful when files are appended chronologically).

    Args:
        path (str): Path to the log file.
        lines (int): Number of lines to return.

    Returns:
        List[str]: Lines in newest-first order.
    """
    from collections import deque

    buf = deque(maxlen=lines)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                buf.append(ln.rstrip("\n"))
    except FileNotFoundError:
        return []

    # buf contains oldest->newest; reverse to return newest first
    return list(reversed(buf))


if __name__ == "__main__":
    # Simple CLI to print newest-first log lines
    import argparse

    parser = argparse.ArgumentParser(description="Print log lines newest-first")
    parser.add_argument("path", nargs="?", default="logs/inventory_system.log")
    parser.add_argument("-n", "--lines", type=int, default=100)
    args = parser.parse_args()

    for line in read_log_tail_reverse(args.path, args.lines):
        print(line)
