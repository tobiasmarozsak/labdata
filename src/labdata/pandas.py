from functools import wraps

import pandas as pd
import wrapt

from labdata import config
from labdata.tools.mapping import ravel


@wrapt.decorator
def init(wrapped, instance, args, kwargs):
    data = args[0] if args else kwargs.pop("data", None)
    if isinstance(data, dict):
        data = ravel(data)
    elif isinstance(data, list):
        data = [ravel(item) if isinstance(item, dict) else item for item in data]
    return wrapped(data, *args[1:], **kwargs)


@wrapt.decorator
def getitem(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    except KeyError:
        key = args[0] if args else kwargs["key"]
        if not isinstance(key, str):
            raise
        prefix = key + config.SEPARATOR
        columns = [
            column for column in instance.columns
            if isinstance(column, str) and column.startswith(prefix)
        ]
        if not columns:
            raise

    result = wrapped(columns).copy()
    result.columns = [column[len(prefix):] for column in columns]
    return result


pd.DataFrame.__init__ = init(pd.DataFrame.__init__)
pd.DataFrame.__getitem__ = getitem(pd.DataFrame.__getitem__)


class CachedAccessor:
    _accessor_name = None

    def __new__(cls, data):
        accessor = data.__dict__.get(cls._accessor_name)
        if isinstance(accessor, cls):
            return accessor
        accessor = super().__new__(cls)
        data.__dict__[cls._accessor_name] = accessor
        return accessor

    def __init__(self, data):
        if hasattr(self, "_data"):
            return
        self._data = data


_ACCESSORS = {}


def _accessor(name, base=CachedAccessor):
    if name not in _ACCESSORS:
        cls = type(f"{name.title()}Accessor", (base,), {"_accessor_name": name})
        pd.api.extensions.register_dataframe_accessor(name)(cls)
        _ACCESSORS[name] = cls
    return _ACCESSORS[name]


def register(func=None, *, accessor):
    if func is None:
        return lambda wrapped: register(wrapped, accessor=accessor)

    cls = _accessor(accessor)

    if hasattr(cls, func.__name__):
        previous = getattr(cls, func.__name__)
        print(
            f"DataFrame function '.{accessor}.{func.__name__}' is already registered; "
            f"replacing {previous.__module__}.{previous.__qualname__} with "
            f"{func.__module__}.{func.__qualname__}."
        )

    @wraps(func)
    def registered(self, *args, **kwargs):
        return func(self._data, *args, **kwargs)

    setattr(cls, func.__name__, registered)
    return func
