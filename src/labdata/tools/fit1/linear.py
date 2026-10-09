import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def linear(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, gradient, intercept):
    return gradient * x + intercept


def guess(x, y):
    return {
        "gradient": 0,
        "intercept": np.mean(y),
    }
