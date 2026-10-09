import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def multiexponential(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    result = lsfit(x, y, fun=model, p0=p0, **kwargs)
    for key in ("var", "uvar"):
        p = result[key]
        total = p["amplitude1"] + p["amplitude2"]
        p["fraction1"] = p["amplitude1"] / total
        p["fraction2"] = p["amplitude2"] / total
    return result


def model(x, lifetime1, lifetime2, amplitude1, amplitude2, offset):
    return (offset + amplitude1 * np.exp(-x / lifetime1)
            + amplitude2 * np.exp(-x / lifetime2))


def guess(x, y):
    order = np.argsort(x)
    amplitude = y[order[0]] - y[order[-1]]
    span = np.ptp(x)
    return {
        "amplitude1": amplitude / 2,
        "amplitude2": amplitude / 2,
        "lifetime1": {"value": span / 10, "min": np.finfo(float).eps},
        "lifetime2": {"value": span / 2, "min": np.finfo(float).eps},
        "offset": y[order[-1]],
    }
