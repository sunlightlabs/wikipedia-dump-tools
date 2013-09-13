import sys

__all__ = ['progress']

PROGRESS_CHARS = list(reversed(['|', '/', '-', '\\']))
PROGRESS_CHARS_LEN = len(PROGRESS_CHARS)
def progress(i):
    sys.stdout.write("\x1B[1D")
    sys.stdout.write(PROGRESS_CHARS[i % PROGRESS_CHARS_LEN])
    sys.stdout.flush()

