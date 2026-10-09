import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def sinusoid(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    result = lsfit(x, y, fun=model, p0=p0, **kwargs)
    for key in ("var", "uvar"):
        result[key]["period"] = 1 / result[key]["frequency"]
    return result


def model(x, amplitude, frequency, phase, offset):
    return amplitude * np.sin(2 * np.pi * frequency * x + phase) + offset


def spectrum(x, y):
    order = np.argsort(x)
    grid = np.linspace(np.min(x), np.max(x), len(x))
    signal = np.interp(grid, x[order], y[order])
    coefficients = np.fft.rfft(signal - np.mean(signal))[1:]
    frequencies = np.fft.rfftfreq(len(grid), grid[1] - grid[0])[1:]
    return frequencies, coefficients


def guess(x, y):
    frequencies, coefficients = spectrum(x, y)
    peak = np.argmax(np.abs(coefficients))
    frequency = frequencies[peak]
    phase = np.angle(coefficients[peak]) + np.pi / 2 - 2 * np.pi * frequency * np.min(x)
    return {
        "amplitude": np.ptp(y) / 2,
        "frequency": {"value": frequency, "min": 0},
        "phase": phase,
        "offset": np.mean(y),
    }
