import matplotlib as mpl
import numpy as np
from pandas.api.types import is_numeric_dtype

from labdata.plots.core import figure, label, name, register


@register
@figure("wikilight")
def errorbar(data, x, y, z=None, cmap=None, vmin=None, vmax=None,
             norm=None, ax=None, **kwargs):
    kwargs.setdefault("alpha", 1)
    kwargs.setdefault("elinewidth", 2)
    fields = [x, y] if z is None else [x, y, z]
    groups = [x] if z is None else [x, z]
    values = data[fields].dropna().groupby(groups, as_index=False)[y].agg(list)

    statistics = []
    for samples in values[y]:
        mean = np.nanmean(samples)
        statistics.append(
            (mean.n, mean.s) if hasattr(mean, "n") else (mean, np.nanstd(samples))
        )
    values["mean"], values["std"] = zip(*statistics)

    artists = []
    if z is None:
        artists.append(ax.errorbar(
            values[x].to_numpy(), values["mean"].to_numpy(),
            yerr=values["std"].to_numpy(), **kwargs,
        ))
    else:
        numeric = is_numeric_dtype(values[z])
        if numeric and cmap is not None:
            cmap = mpl.colormaps.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin, vmax) if norm is None else norm
            norm.autoscale_None(values[z].to_numpy())

        for value, group in values.groupby(z):
            options = kwargs.copy()
            if numeric and cmap is not None:
                options["color"] = cmap(norm(value))
            group_label = f"{value:.3g}" if numeric else str(value)
            artist = ax.errorbar(
                group[x].to_numpy(), group["mean"].to_numpy(),
                yerr=group["std"].to_numpy(), label=group_label, **options,
            )
            for bar in artist[2]:
                bar.set_alpha(0.7)
                bar.set_capstyle("round")
            artists.append(artist)

        ax.legend(title=label(z), bbox_to_anchor=(1, 1), loc="upper left")

    ax.grid(True, which="both")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    title = f"errorbar_{name(x)}_vs_{name(y)}"
    if z is not None:
        title += f"_by_{name(z)}"
    ax.set_title(title)

    return artists
