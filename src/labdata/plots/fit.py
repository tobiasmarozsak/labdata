import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from pandas.api.types import is_numeric_dtype

import labdata.tools.fit1 as fit1
from labdata.matplotlib import format_value
from labdata.plots.core import register


@register
def fit(data, x, y, fun, z=None, p0=None, ax=None, **kwargs):
    if ax is None:
        ax = plt.gca()

    fields = [x, y] if z is None else [x, y, z]
    values = data[fields].dropna()
    function = getattr(fit1, fun) if isinstance(fun, str) else fun
    name = fun if isinstance(fun, str) else fun.__name__
    grouped = z is not None
    groups = values.groupby(z, sort=True) if grouped else [(None, values)]
    numeric = grouped and is_numeric_dtype(values[z])
    data_legend = ax.get_legend()
    data_lines = {line.get_label(): line for line in ax.lines}
    for container in ax.containers:
        lines = getattr(container, "lines", ())
        if lines and lines[0] is not None:
            data_lines[container.get_label()] = lines[0]
    handles, labels = [], []

    for value, group in groups:
        result = function(
            np.asarray(group[x]),
            np.asarray(group[y]),
            p0=p0,
        )
        xfit = np.linspace(np.min(result["x"]), np.max(result["x"]), 1000)
        yfit = result["fun"](x=xfit, **result["popt"])

        group_label = f"{value:.3g}" if numeric else str(value)
        reference = data_lines.get(group_label) if grouped else next(
            reversed(ax.lines), None
        )
        options = kwargs.copy()
        options.setdefault("marker", "none")
        options.setdefault("lw", 2)
        options.setdefault("ls", "-")
        options.setdefault("alpha", 0.65)
        if reference is not None:
            if "color" not in options and "c" not in options:
                options["color"] = reference.get_color()
            options.setdefault("zorder", reference.get_zorder() - 1)

        fit_label = r"$\bf{" + name.replace("_", r"\_") + "}$"
        if grouped:
            fit_label += f" ({group_label})"
        line, = ax.plot(xfit, yfit, label=fit_label, **options)

        rows = []
        for key, parameter in result["uvar"].items():
            field, parameter = format_value(key, parameter)
            rows.append((f"{field}:", parameter))
        width = max(len(key) for key, _ in rows)
        parameters = "\n".join(
            f"{key:<{width}} {parameter}" for key, parameter in rows
        )
        handles += [line, Line2D([], [], alpha=0)]
        labels += [fit_label, parameters]

    position = 1
    if data_legend is not None:
        ax.add_artist(data_legend)
        ax.figure.canvas.draw()
        bounds = ax.transAxes.inverted().transform(data_legend.get_window_extent())
        position = bounds[0, 1] - 0.02

    legend = ax.legend(
        handles, labels, bbox_to_anchor=(1, position), loc="upper left"
    )
    if data_legend is not None:
        source = data_legend.get_frame()
        legend.get_frame().set(
            facecolor=source.get_facecolor(),
            edgecolor=source.get_edgecolor(),
            linewidth=source.get_linewidth(),
            alpha=source.get_alpha(),
            boxstyle=source.get_boxstyle(),
        )
    for text in legend.get_texts():
        text.set_family("monospace")
    ax.grid(True, which="both")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
