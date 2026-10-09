import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def lorentzian(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, centre, gamma, height, offset):
    return offset + height * (gamma / 2)**2 / ((x - centre)**2 + (gamma / 2)**2)


def guess(x, y):
    order = np.argsort(x)
    x, y = x[order], y[order]
    offset = np.min(y)
    height = np.max(y) - offset
    peak = y > offset + height / 2
    gamma = np.sum(np.abs(np.gradient(x))[peak])
    return {
        "centre": x[np.argmax(y)],
        "gamma": {"value": gamma, "min": np.finfo(float).eps},
        "height": height,
        "offset": offset,
    }
