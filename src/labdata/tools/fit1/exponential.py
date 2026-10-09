import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def exponential(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, lifetime, amplitude, offset):
    return offset + amplitude * np.exp(-x / lifetime)


def guess(x, y):
    order = np.argsort(x)
    amplitude = y[order[0]] - y[order[-1]]
    lifetime = np.ptp(x) / 3
    return {
        "amplitude": amplitude * np.exp(np.min(x) / lifetime),
        "lifetime": {"value": lifetime, "min": np.finfo(float).eps},
        "offset": y[order[-1]],
    }
