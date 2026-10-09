import warnings
from collections import OrderedDict
from collections.abc import Mapping
from copy import deepcopy
from functools import wraps
from inspect import signature

import joblib
import numpy as np
import pandas as pd

from labdata.pandas import register as _register
from labdata.progress import progress
from labdata.tools.mapping import ravel, unravel


def register(func=None, *, accessor="m"):
    return _register(func, accessor=accessor)


def copy(value):
    if isinstance(value, Mapping):
        return {key: copy(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        view = value.view()
        view.flags.writeable = False
        return view
    return value


def method(vectorise=False):
    def decorator(func):
        @wraps(func)
        def wrapper(data, *args, **kwargs):
            # DataFrames cross the method boundary as ordinary nested records.
            frame = data if isinstance(data, pd.DataFrame) else None
            if frame is not None:
                data = [unravel(record) for record in frame.to_dict("records")]

            positions = None
            if isinstance(data, list):
                data = [copy(record) for record in data]
                if vectorise:
                    result, positions, failures = [], [], []
                    items = progress(data, desc=func.__name__)
                    for position, record in enumerate(items):
                        try:
                            item = func(record, *args, **kwargs)
                        except Exception as error:
                            identity = (
                                record.get("FILE")
                                if isinstance(record, Mapping) else None
                            )
                            if identity is None:
                                identity = (
                                    frame.index[position]
                                    if frame is not None else position
                                )
                            failures.append((identity, error))
                        else:
                            result.append(item)
                            positions.append(position)
                    if failures:
                        details = "\n".join(
                            f"- {identity}: {type(error).__name__}: {error}"
                            for identity, error in failures
                        )
                        warnings.warn(
                            f"{func.__name__} skipped {len(failures)} of "
                            f"{len(data)} records:\n{details}",
                            RuntimeWarning,
                            stacklevel=2,
                        )
                else:
                    result = func(data, *args, **kwargs)
            else:
                data = copy(data)
                result = func(data, *args, **kwargs)

            records = result if isinstance(result, list) else [result]
            for record in records:
                if isinstance(record, dict):
                    record["METHOD"] = func.__name__

            # Convert record results back only when the input was a DataFrame.
            if frame is not None:
                if isinstance(result, dict):
                    result = pd.Series(ravel(result))
                elif isinstance(result, list) and all(isinstance(item, dict) for item in result):
                    if result:
                        if positions is not None:
                            index = frame.index.take(positions)
                        else:
                            index = frame.index if len(result) == len(frame) else None
                        result = pd.DataFrame(result, index=index)
                    else:
                        result = frame.iloc[:0].copy()
                    result.attrs = frame.attrs.copy()
            return result

        return wrapper

    return decorator


def cache(maxsize=128):
    def decorator(func):
        sig = signature(func)
        values = OrderedDict()

        @wraps(func)
        def wrapper(*args, **kwargs):
            if maxsize <= 0:
                return func(*args, **kwargs)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            key = joblib.hash(bound.arguments)

            if key not in values:
                values[key] = deepcopy(func(*args, **kwargs))
                if len(values) > maxsize:
                    values.popitem(last=False)

            values.move_to_end(key)
            return deepcopy(values[key])

        return wrapper

    return decorator
