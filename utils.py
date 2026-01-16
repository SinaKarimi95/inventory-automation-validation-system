# utils.py

from datetime import datetime


def timestamp():
    # Return current timestamp as a formatted string
    return datetime.now().strftime("%Y-%m-%d %H:%M")
