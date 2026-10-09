from collections.abc import Mapping

import numpy as np

from labdata import config, tools
from labdata.plots.core import register, subplot
from labdata.tools.mapping import unravel


def _subtree(record, path):
    if path in record and isinstance(record[path], Mapping):
        return record[path]
    prefix = path + config.SEPARATOR
    return unravel({
        key[len(prefix):]: value
        for key, value in record.items()
        if isinstance(key, str) and key.startswith(prefix)
    })


def _centre(image, mode, result):
    parameters = {} if result is None else result["popt"]
    if "x_centre" in parameters and "y_centre" in parameters:
        return np.array([parameters["y_centre"], parameters["x_centre"]])
    if mode == "XS" and "centre" in parameters:
        return np.array([0, parameters["centre"]])
    if mode == "YS" and "centre" in parameters:
        return np.array([parameters["centre"], 0])
    return np.asarray(tools.inversion_centre(image))


def _radialmean(image, centre, nbins):
    rows, columns = np.indices(image.shape)
    radius = np.hypot(rows - centre[0], columns - centre[1]).ravel()
    values = np.asarray(image).ravel()
    edges = np.linspace(0, radius.max(), nbins + 1)
    bins = np.clip(np.digitize(radius, edges) - 1, 0, nbins - 1)
    finite = np.isfinite(values)
    count = np.bincount(bins[finite], minlength=nbins)
    total = np.bincount(bins[finite], weights=values[finite], minlength=nbins)
    mean = np.full(nbins, np.nan)
    np.divide(total, count, out=mean, where=count > 0)
    return (edges[1:] + edges[:-1]) / 2, mean


@register
@subplot
def implot(data, which="X", centre=None, xlim=None, ylim=None, nbins=100,
           fit=None, *, ax, **kwargs):
    mode = which.upper()
    image = np.asarray(data["IMAGE"])
    mask = np.asarray(data.get("MASK", np.ones(image.shape, dtype=bool)), dtype=bool)
    masked = np.where(mask, image, np.nan)
    result = None if fit is None else _subtree(data, fit)
    centre = (
        np.asarray(centre)
        if centre is not None
        else _centre(image, mode, result)
    )
    rows, columns = np.indices(image.shape)

    if mode == "X":
        row = int(np.clip(round(centre[0]), 0, image.shape[0] - 1))
        x = columns[row] - centre[1]
        full, selected = image[row], masked[row]
        coordinates = np.stack((rows[row], columns[row]))
    elif mode == "Y":
        column = int(np.clip(round(centre[1]), 0, image.shape[1] - 1))
        x = rows[:, column] - centre[0]
        full, selected = image[:, column], masked[:, column]
        coordinates = np.stack((rows[:, column], columns[:, column]))
    elif mode == "XS":
        x = columns[0] - centre[1]
        full = np.nansum(image, axis=0)
        selected = np.nansum(masked, axis=0)
        coordinates = columns[0]
    elif mode == "YS":
        x = rows[:, 0] - centre[0]
        full = np.nansum(image, axis=1)
        selected = np.nansum(masked, axis=1)
        coordinates = rows[:, 0]
    elif mode == "R":
        x, full = _radialmean(image, centre, nbins)
        _, selected = _radialmean(masked, centre, nbins)
        coordinates = np.stack((rows, columns))
    else:
        raise ValueError(f"Unknown image profile {which!r}")

    options = {"marker": "none", "ls": "-", "lw": 1.5, **kwargs}
    artists = ax.plot(x, full, **{**options, "color": "black", "alpha": 0.15})
    artists += ax.plot(
        x, selected, **{**options, "color": "black", "alpha": 0.6}
    )
    if result is not None:
        fitted = result["fun"](coordinates, **result["popt"])
        if mode == "R":
            _, fitted = _radialmean(fitted, centre, nbins)
        artists += ax.plot(x, fitted, **{
            **options, "color": "red", "alpha": 0.9, "zorder": 1,
        })

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)
    ax.grid(True)
    ax.set_facecolor("white")
    ax.patch.set_alpha(1)
    return artists
