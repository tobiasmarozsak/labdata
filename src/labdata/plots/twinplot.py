import matplotlib.pyplot as plt

from labdata.plots.core import figure, name, register


@register
@figure("wikilight")
def twinplot(data, x, y, twin, ax=None, **kwargs):
    kwargs.setdefault("alpha", 0.9)
    values = data[[x, y, twin]].dropna()
    colors = kwargs.pop(
        "color", kwargs.pop("c", plt.rcParams["axes.prop_cycle"].by_key()["color"][:2])
    )

    left = kwargs.copy()
    right = kwargs.copy()
    left.setdefault("marker", "o")
    right.setdefault("marker", "s")

    line, = ax.plot(
        values[x].to_numpy(), values[y].to_numpy(), color=colors[0], **left,
    )
    twin_ax = ax.twinx()
    twin_line, = twin_ax.plot(
        values[x].to_numpy(), values[twin].to_numpy(), color=colors[1], **right,
    )

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    twin_ax.set_ylabel(twin)
    ax.grid(True, axis="x")
    ax.set_title(f"plot_{name(x)}_vs_{name(y)}_and_{name(twin)}")

    for axis, artist, symbol in ((ax, line, "●"), (twin_ax, twin_line, "■")):
        axis.annotate(
            symbol, xy=(0.5, 0), xycoords=axis.yaxis.label,
            xytext=(0, -4), textcoords="offset points",
            color=artist.get_color(), ha="center", va="top",
        )

    return line, twin_line
