import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def hyperbola(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, offset, slope):
    return np.sqrt(offset**2 + slope**2 * x**2)


def guess(x, y):
    return {
        "offset": {"value": np.min(np.abs(y)), "min": 0},
        "slope": {"value": np.ptp(y) / np.ptp(x), "min": 0},
    }
