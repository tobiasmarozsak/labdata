from labdata.plots.core import figure, name, register


@register
@figure("wikilight")
def scatter(data, x, y, z=None, ax=None, **kwargs):
    kwargs.setdefault("s", 7**2)
    kwargs.setdefault("alpha", 0.9)
    fields = [x, y] if z is None else [x, y, z]
    values = data[fields].dropna()

    if z is None:
        artist = ax.scatter(values[x].to_numpy(), values[y].to_numpy(), **kwargs)
    else:
        values = values.groupby([x, y], as_index=False)[z].mean()
        artist = ax.scatter(
            values[x].to_numpy(), values[y].to_numpy(),
            c=values[z].to_numpy(), **kwargs,
        )
        colorbar = ax.figure.colorbar(artist, ax=ax)
        colorbar.ax.set_ylabel(z)
        colorbar.ax.set_xticks([])

    ax.grid(True, which="both")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    title = f"scatter_{name(x)}_and_{name(y)}"
    if z is not None:
        title = f"scatter_{name(z)}_vs_{name(x)}_and_{name(y)}"
    ax.set_title(title)

    return artist
