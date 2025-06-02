import os

DEBUG = os.environ.get("DEBUG", "0") == "1"


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)
