import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.special import zeta

from labdata.tools.fit import lsfit
from labdata.tools.fit2.utils import polylog
from labdata.methods.core import cache


@cache()
def becthermal1dfit(image, **kwargs):
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
        sigma = (x_p["sigma"]**2 * y_p["sigma"]**2)**0.25
        height_bec = (x_p["height_bec"]**2 * y_p["height_bec"]**2
                      / (x_p["radius"]**2 * y_p["radius"]**2))**0.25 / (3 * np.pi / 8)
        height_bec *= np.sign(fits["x"]["var"]["height_bec"])
        height_thermal = (x_p["height_thermal"]**2 * y_p["height_thermal"]**2
                          / (x_p["sigma"]**2 * y_p["sigma"]**2))**0.25
        height_thermal *= np.sign(fits["x"]["var"]["height_thermal"])
        height_thermal /= np.sqrt(2 * np.pi) * zeta(2.5) / zeta(2)
        pixelsum_bec = 2 * np.pi / 5 * height_bec * radius**2
        pixelsum_thermal = 2 * np.pi * zeta(3) / zeta(2) * height_thermal * sigma**2
        pixelsum = pixelsum_bec + pixelsum_thermal
        result[key] = {
            "x_centre": x_p["centre"],
            "y_centre": y_p["centre"],
            "x_sigma": x_p["sigma"],
            "y_sigma": y_p["sigma"],
            "sigma": sigma,
            "x_radius": x_p["radius"],
            "y_radius": y_p["radius"],
            "radius": radius,
            "height_bec": height_bec,
            "height_thermal": height_thermal,
            "offset": 0.5 * (x_p["offset"] / image.shape[0]
                             + y_p["offset"] / image.shape[1]),
            "pixelsum_bec": pixelsum_bec,
            "pixelsum_thermal": pixelsum_thermal,
            "pixelsum": pixelsum,
            "becfraction": pixelsum_bec / pixelsum,
        }
    return result


def model(x, centre, sigma, radius, height_bec, height_thermal, offset):
    return (offset
            + height_thermal * polylog(2.5, np.exp(-0.5 * ((x - centre) / sigma)**2)) / zeta(2.5)
            + height_bec * np.maximum(0, 1 - ((x - centre) / radius)**2)**2)


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
        "sigma": {"value": width / np.sqrt(8 * np.log(2)), "min": np.finfo(float).eps},
        "radius": {"value": radius, "min": np.finfo(float).eps},
        "height_bec": height / 2,
        "height_thermal": height / 2,
        "offset": offset,
    }
