import numpy as np

from labdata.tools.fit import lsfit
from labdata.tools.fit2.bec1dfit import bec1dfit
from labdata.methods.core import cache


@cache()
def bec2dfit(image, p0=None, **kwargs):
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
        p["pixelsum"] = 2 * np.pi / 5 * p["height"] * p["radius"]**2
    return result


def model(x, x_centre, y_centre, x_radius, y_radius, height, offset):
    return offset + height * np.maximum(
        0, 1 - ((x[0] - y_centre) / y_radius)**2 - ((x[1] - x_centre) / x_radius)**2
    )**1.5


def guess(image):
    p = bec1dfit(image)["var"]
    return {
        "x_centre": p["x_centre"],
        "y_centre": p["y_centre"],
        "x_radius": {"value": p["x_radius"], "min": np.finfo(float).eps},
        "y_radius": {"value": p["y_radius"], "min": np.finfo(float).eps},
        "height": p["height"],
        "offset": p["offset"],
    }
