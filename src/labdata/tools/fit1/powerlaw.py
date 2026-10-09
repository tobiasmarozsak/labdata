import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def powerlaw(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, a, exponent):
    return a * x**exponent


def guess(x, y):
    return {
        "a": 1,
        "exponent": 1,
    }
