import numpy as np
from labdata.tools.fit1.sinusoid import spectrum

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def sinusoid_beat(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, amplitude, freq_carrier, phase_carrier, freq_envelope, phase_envelope, offset):
    return (offset + amplitude * np.sin(2 * np.pi * freq_envelope * x + phase_envelope)
            * np.sin(2 * np.pi * freq_carrier * x + phase_carrier))


def guess(x, y):
    frequencies, coefficients = spectrum(x, y)
    peaks = np.argsort(np.abs(coefficients))[-2:]
    low, high = np.sort(frequencies[peaks])
    return {
        "amplitude": np.ptp(y) / 2,
        "offset": np.mean(y),
        "freq_carrier": {"value": (high + low) / 2, "min": 0},
        "freq_envelope": {"value": (high - low) / 2, "min": 0},
        "phase_carrier": 0,
        "phase_envelope": 0,
    }
