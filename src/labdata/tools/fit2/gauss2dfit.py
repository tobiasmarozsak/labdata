import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def gauss2dfit(image, p0=None, **kwargs):
    image = np.asarray(image)
    x = np.indices(image.shape).reshape(2, -1)
    y = image.ravel()
    if p0 is None:
        p0 = guess(x, y)
    weights = kwargs.pop("weights", None)
    if weights is not None:
        kwargs["weights"] = np.broadcast_to(weights, image.shape).ravel()
    fit = lsfit(x, y, fun=model, p0=p0, **kwargs)
    result = {"xy_fit": fit, "var": fit["var"].copy(), "uvar": fit["uvar"].copy()}
    for key in ("var", "uvar"):
        p = result[key]
        p["sigma"] = (p["x_sigma"]**2 * p["y_sigma"]**2)**0.25
        p["pixelsum"] = 2 * np.pi * p["height"] * p["sigma"]**2
    return result


def model(x, x_centre, y_centre, x_sigma, y_sigma, height, offset):
    return offset + height * np.exp(
        -0.5 * ((x[0] - y_centre) / y_sigma)**2
        -0.5 * ((x[1] - x_centre) / x_sigma)**2
    )


def guess(x, y):
    finite = np.isfinite(y)
    x, y = x[:, finite], y[finite]
    offset = np.min(y)
    signal = y - offset
    total = np.sum(signal)
    centre = np.sum(x * signal, axis=1) / total
    variance = np.sum((x - centre[:, None])**2 * signal, axis=1) / total
    sigma = np.sqrt(np.maximum(variance, np.finfo(float).eps))
    return {
        "x_centre": centre[1],
        "y_centre": centre[0],
        "x_sigma": {"value": sigma[1], "min": np.finfo(float).eps},
        "y_sigma": {"value": sigma[0], "min": np.finfo(float).eps},
        "height": {"value": np.max(signal), "min": 0},
        "offset": offset,
    }
