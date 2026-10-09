import numpy as np

from labdata.plots.core import figure, name, register


def _edges(values, scale):
    values = np.asarray(values, dtype=float)
    if scale == "linear":
        middle = (values[1:] + values[:-1]) / 2
    elif scale == "log":
        middle = np.sqrt(values[1:] * values[:-1])
    else:
        raise NotImplementedError(scale)

    if len(values) == 1:
        return values + np.array([-0.5, 0.5])
    if scale == "linear":
        return np.r_[2 * values[0] - middle[0], middle,
                     2 * values[-1] - middle[-1]]
    return np.r_[values[0] ** 2 / middle[0], middle,
                 values[-1] ** 2 / middle[-1]]


@register
@figure("wikilight")
def pcolormesh(data, x, y, z, xscale="linear", yscale="linear",
               ax=None, **kwargs):
    values = (
        data[[x, y, z]]
        .dropna()
        .groupby([x, y], as_index=False)[z]
        .mean()
    )
    grid = (
        values.pivot(index=y, columns=x, values=z)
        .sort_index(axis=0)
        .sort_index(axis=1)
    )

    kwargs.setdefault("vmin", np.nanmin(grid.to_numpy()))
    kwargs.setdefault("vmax", np.nanmax(grid.to_numpy()))
    kwargs.setdefault("edgecolor", "black")
    kwargs.setdefault("linewidth", 0.5)

    ax.set_facecolor("darkgrey")
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    artist = ax.pcolormesh(
        _edges(grid.columns, xscale),
        _edges(grid.index, yscale),
        grid.to_numpy(),
        **kwargs,
    )
    colorbar = ax.figure.colorbar(artist, ax=ax)
    colorbar.ax.set_ylabel(z)
    colorbar.ax.set_xticks([])
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"colormesh_{name(z)}_vs_{name(x)}_and_{name(y)}")

    return artist
