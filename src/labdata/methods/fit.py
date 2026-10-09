import numpy as np

import labdata.tools.fit2 as fit2
from labdata.methods.core import method, register


def fit(data, function, **kwargs):
    image = data["IMAGE"]
    if "MASK" in data:
        image = np.where(data["MASK"], image, np.nan)
    result = function(image, **kwargs)
    roi = data.get("METADATA", {}).get(
        "ROI",
        (0, image.shape[0], 0, image.shape[1]),
    )
    for name in ("var", "uvar"):
        values = result[name].copy()
        values["x_centre"] += roi[2]
        values["y_centre"] += roi[0]
        values = {
            f"{key}[pixel]"
            if any(name in key for name in ("centre", "sigma", "radius"))
            else key: value
            for key, value in values.items()
        }
        data.setdefault(name, {}).update(values)
    data.update(
        {key: value for key, value in result.items() if key not in ("var", "uvar")}
    )
    return data


@register
@method(vectorise=True)
def gauss1dfit(data, **kwargs):
    return fit(data, fit2.gauss1dfit, **kwargs)


@register
@method(vectorise=True)
def gauss2dfit(data, **kwargs):
    return fit(data, fit2.gauss2dfit, **kwargs)


@register
@method(vectorise=True)
def bec1dfit(data, **kwargs):
    return fit(data, fit2.bec1dfit, **kwargs)


@register
@method(vectorise=True)
def bec2dfit(data, **kwargs):
    return fit(data, fit2.bec2dfit, **kwargs)


@register
@method(vectorise=True)
def becthermal1dfit(data, **kwargs):
    return fit(data, fit2.becthermal1dfit, **kwargs)


@register
@method(vectorise=True)
def becthermal2dfit(data, **kwargs):
    return fit(data, fit2.becthermal2dfit, **kwargs)
