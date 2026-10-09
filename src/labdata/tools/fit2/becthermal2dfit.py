import numpy as np
from scipy.special import zeta

from labdata.tools.fit import lsfit
from labdata.tools.fit2.utils import polylog
from labdata.tools.fit2.becthermal1dfit import becthermal1dfit
from labdata.methods.core import cache


@cache()
def becthermal2dfit(image, p0=None, **kwargs):
    image = np.asarray(image)
    x = np.indices(image.shape).reshape(2, -1)
    y = image.ravel()
    if p0 is None:
        p0 = guess(image)
    weights = kwargs.pop("weights", None)
    if weights is not None:
        kwargs["weights"] = np.broadcast_to(weights, image.shape).ravel()
    fit = lsfit(x, y, fun=model, p0=p0, **kwargs)
    result = {"xy_fit": fit, "var": fit["var"].copy(), "uvar": fit["uvar"].copy()}
    for key in ("var", "uvar"):
        p = result[key]
        p["radius"] = (p["x_radius"]**2 * p["y_radius"]**2)**0.25
        p["sigma"] = (p["x_sigma"]**2 * p["y_sigma"]**2)**0.25
        p["pixelsum_bec"] = 2 * np.pi / 5 * p["height_bec"] * p["radius"]**2
        p["pixelsum_thermal"] = 2 * np.pi * zeta(3) / zeta(2) * p["height_thermal"] * p["sigma"]**2
        p["pixelsum"] = p["pixelsum_bec"] + p["pixelsum_thermal"]
        p["becfraction"] = p["pixelsum_bec"] / p["pixelsum"]
    return result


def model(x, x_centre, y_centre, x_sigma, y_sigma, x_radius, y_radius,
          height_bec, height_thermal, offset):
    thermal = polylog(2, np.exp(
        -0.5 * ((x[0] - y_centre) / y_sigma)**2
        -0.5 * ((x[1] - x_centre) / x_sigma)**2
    )) / zeta(2)
    bec = np.maximum(
        0, 1 - ((x[0] - y_centre) / y_radius)**2 - ((x[1] - x_centre) / x_radius)**2
    )**1.5
    return offset + height_thermal * thermal + height_bec * bec


def guess(image):
    p = becthermal1dfit(image)["var"]
    return {
        "x_centre": p["x_centre"],
        "y_centre": p["y_centre"],
        "x_sigma": {"value": p["x_sigma"], "min": np.finfo(float).eps},
        "y_sigma": {"value": p["y_sigma"], "min": np.finfo(float).eps},
        "x_radius": {"value": p["x_radius"], "min": np.finfo(float).eps},
        "y_radius": {"value": p["y_radius"], "min": np.finfo(float).eps},
        "height_bec": p["height_bec"],
        "height_thermal": p["height_thermal"],
        "offset": p["offset"],
    }
