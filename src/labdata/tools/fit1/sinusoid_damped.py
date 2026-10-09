import numpy as np
from labdata.tools.fit1.sinusoid import guess as sinusoid_guess

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def sinusoid_damped(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, amplitude, frequency, phase, lifetime, offset):
    return offset + amplitude * np.exp(-x / lifetime) * np.sin(2 * np.pi * frequency * x + phase)


def guess(x, y):
    p0 = sinusoid_guess(x, y)
    p0["lifetime"] = {"value": np.ptp(x), "min": np.finfo(float).eps}
    return p0
