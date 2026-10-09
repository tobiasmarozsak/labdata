import numpy as np

from labdata.plots.core import figure, name, register


@register
@figure("wikilight")
def hist(data, x, ax=None, **kwargs):
    values = data[x].dropna().to_numpy()
    count = len(values)
    mean = np.mean(values)
    std = np.std(values)

    artists = ax.hist(values, zorder=2, **kwargs)
    ax.grid(True, which="both")
    ax.axvline(mean, c="black", marker="none", ls="--")
    ax.axvline(mean - std, c="gray", marker="none", alpha=0.3, zorder=0)
    ax.axvline(mean + std, c="gray", marker="none", alpha=0.3, zorder=0)
    ax.axvspan(mean - std, mean + std, color="gray", alpha=0.3, zorder=0)

    text = (
        f"N = {count}\n$\\mu$ = {mean:.2E}\n$\\sigma$ = {std:.2E}\n"
        f"$\\sigma$/$\\mu$ = {std / mean * 100:.1f}%"
    )
    ax.legend([], title=text, bbox_to_anchor=(1, 1), loc="upper left")
    ax.set_xlabel(x)
    ax.set_ylabel("Counts")
    ax.set_title(f"hist_{name(x)}")

    return artists
