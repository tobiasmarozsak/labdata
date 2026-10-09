import matplotlib as mpl
import pandas as pd

from labdata.plots.core import figure, label, name, register


@register
@figure("wikilight")
def plot(data, x, y, z=None, cmap=None, vmin=None, vmax=None,
         norm=None, ax=None, **kwargs):
    kwargs.setdefault("alpha", 0.9)
    fields = [x, y] if z is None else [x, y, z]
    values = data[fields].dropna()

    artists = []
    if z is None:
        artists += ax.plot(values[x].to_numpy(), values[y].to_numpy(), **kwargs)
    else:
        numeric = pd.api.types.is_numeric_dtype(values[z])
        if numeric and cmap is not None:
            cmap = mpl.colormaps.get_cmap(cmap)
            norm = mpl.colors.Normalize(vmin, vmax) if norm is None else norm
            norm.autoscale_None(values[z].to_numpy())

        for value, group in values.groupby(z):
            options = kwargs.copy()
            if numeric and cmap is not None:
                options["color"] = cmap(norm(value))
            group_label = f"{value:.3g}" if numeric else str(value)
            artists += ax.plot(
                group[x].to_numpy(), group[y].to_numpy(),
                label=group_label, **options,
            )

        ax.legend(title=label(z), bbox_to_anchor=(1, 1), loc="upper left")

    ax.grid(True, which="both")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    title = f"plot_{name(x)}_vs_{name(y)}"
    if z is not None:
        title += f"_by_{name(z)}"
    ax.set_title(title)

    return artists
