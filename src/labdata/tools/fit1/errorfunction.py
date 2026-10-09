import numpy as np
from scipy.special import erf

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def errorfunction(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, amplitude, sigma, mu, offset):
    return amplitude * erf((x - mu) / (np.sqrt(2) * sigma)) + offset


def guess(x, y):
    order = np.argsort(x)
    x, y = x[order], y[order]
    gradient = np.gradient(y, x)
    peak = np.argmax(np.abs(gradient))
    amplitude = np.sign(gradient[peak]) * np.ptp(y) / 2
    sigma = abs(amplitude * np.sqrt(2 / np.pi) / gradient[peak])
    return {
        "amplitude": amplitude,
        "offset": (np.max(y) + np.min(y)) / 2,
        "mu": x[peak],
        "sigma": {"value": sigma, "min": np.finfo(float).eps},
    }
