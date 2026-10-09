import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def gaussian(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, centre, sigma, height, offset):
    return offset + height * np.exp(-0.5 * ((x - centre) / sigma)**2)


def guess(x, y):
    order = np.argsort(x)
    x, y = x[order], y[order]
    offset = np.min(y)
    height = np.max(y) - offset
    peak = y > offset + height / 2
    width = np.sum(np.abs(np.gradient(x))[peak]) / np.sqrt(8 * np.log(2))
    return {
        "centre": x[np.argmax(y)],
        "height": height,
        "offset": offset,
        "sigma": {"value": width, "min": np.finfo(float).eps},
    }
