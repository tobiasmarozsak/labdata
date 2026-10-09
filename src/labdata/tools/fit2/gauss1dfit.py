import numpy as np
from scipy.ndimage import gaussian_filter

from labdata.tools.fit import lsfit
from labdata.tools.fit1.gaussian import model
from labdata.methods.core import cache


@cache()
def gauss1dfit(image, **kwargs):
    image = np.asarray(image)
    fits = {}
    for name, axis in (("x", 0), ("y", 1)):
        y = np.sum(image, axis=axis)
        x = np.arange(len(y))
        p0 = guess(x, y)
        fits[name] = lsfit(x, y, fun=model, p0=p0, **kwargs)

    result = {"x_fit": fits["x"], "y_fit": fits["y"]}
    opposite = fits["x"]["var"]["height"] * fits["y"]["var"]["height"] < 0
    for key in ("var", "uvar"):
        x_p = fits["x"][key]
        y_p = fits["y"][key]
        sigma = (x_p["sigma"]**2 * y_p["sigma"]**2)**0.25
        if opposite:
            height = 0 * x_p["height"]
        else:
            height = (x_p["height"] * y_p["height"]
                      / (x_p["sigma"] * y_p["sigma"])
                      / (2 * np.pi))**0.5
            height *= np.sign(fits["x"]["var"]["height"])
        offset = 0.5 * (x_p["offset"] / image.shape[0]
                        + y_p["offset"] / image.shape[1])
        result[key] = {
            "x_centre": x_p["centre"],
            "y_centre": y_p["centre"],
            "x_sigma": x_p["sigma"],
            "y_sigma": y_p["sigma"],
            "sigma": sigma,
            "height": height,
            "offset": offset,
            "pixelsum": 2 * np.pi * height * sigma**2,
        }
    return result


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
    return {
        "centre": x[np.argmax(sign * y)],
        "sigma": {"value": width / np.sqrt(8 * np.log(2)), "min": np.finfo(float).eps},
        "height": height,
        "offset": offset,
    }
