import numpy as np
from scipy.ndimage import gaussian_filter

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def bec1dfit(image, **kwargs):
    image = np.asarray(image)
    fits = {}
    for name, axis in (("x", 0), ("y", 1)):
        y = np.sum(image, axis=axis)
        x = np.arange(len(y))
        fits[name] = lsfit(x, y, fun=model, p0=guess(x, y), **kwargs)

    result = {"x_fit": fits["x"], "y_fit": fits["y"]}
    for key in ("var", "uvar"):
        x_p, y_p = fits["x"][key], fits["y"][key]
        radius = (x_p["radius"]**2 * y_p["radius"]**2)**0.25
        height = (x_p["height"]**2 * y_p["height"]**2
                  / (x_p["radius"]**2 * y_p["radius"]**2))**0.25 / (3 * np.pi / 8)
        height *= np.sign(fits["x"]["var"]["height"])
        result[key] = {
            "x_centre": x_p["centre"],
            "y_centre": y_p["centre"],
            "x_radius": x_p["radius"],
            "y_radius": y_p["radius"],
            "radius": radius,
            "height": height,
            "offset": 0.5 * (x_p["offset"] / image.shape[0]
                             + y_p["offset"] / image.shape[1]),
            "pixelsum": 2 * np.pi / 5 * height * radius**2,
        }
    return result


def model(x, centre, radius, height, offset):
    return offset + height * np.maximum(0, 1 - ((x - centre) / radius)**2)**2


def guess(x, y):
    finite = np.isfinite(y)
    x, y = x[finite], y[finite]
    y = gaussian_filter(y, sigma=1)
    deviation = y - (y[0] + y[-1]) / 2
    sign = np.sign(deviation[np.argmax(np.abs(deviation))])
    offset = sign * np.min(sign * y)
    height = sign * np.ptp(y)
    peak = sign * (y - offset) > abs(height) / 2
    width = np.sum(np.abs(np.gradient(x))[peak])
    radius = width / (2 * np.sqrt(1 - 2**-0.5))
    return {
        "centre": x[np.argmax(sign * y)],
        "radius": {"value": radius, "min": np.finfo(float).eps},
        "height": height,
        "offset": offset,
    }
