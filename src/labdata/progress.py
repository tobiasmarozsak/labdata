from contextlib import contextmanager
from contextvars import ContextVar

from tqdm import tqdm


_ENABLED = ContextVar("progress_enabled", default=True)
_DEPTH = ContextVar("progress_depth", default=0)


@contextmanager
def progressbar(enabled=True):
    token = _ENABLED.set(enabled)
    try:
        yield
    finally:
        _ENABLED.reset(token)


def progress(iterable, **kwargs):
    depth = _DEPTH.get()
    token = _DEPTH.set(depth + 1)
    try:
        items = tqdm(iterable, **kwargs) if _ENABLED.get() and depth == 0 else iterable
        yield from items
    finally:
        _DEPTH.reset(token)
