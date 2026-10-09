from functools import wraps
from typing import NamedTuple

import matplotlib.pyplot as plt
import pandas as pd

from labdata import config
from labdata.pandas import CachedAccessor, _accessor, register as _register


class PlotLayout(NamedTuple):
    figure: object
    axes: tuple


def register(func=None, *, accessor="p"):
    return _register(func, accessor=accessor)


def name(field):
    return str(field).split(config.SEPARATOR)[-1].split("[", 1)[0].strip()


def label(field):
    return str(field).split(config.SEPARATOR)[-1].replace("[", " [", 1)


def title(data):
    return config.PLOT_TITLE(data)


def metadata(data):
    values = {}
    if "FILE" in data:
        values["FILE"] = [
            file
            for value in data["FILE"].dropna()
            for file in (value if isinstance(value, list) else [value])
        ]
    if "METHOD" in data:
        values["METHOD"] = data["METHOD"].dropna().tolist()
    return values


def figure(style, *, subplots=False):
    def decorator(func):
        @wraps(func)
        def wrapper(data, *args, **kwargs):
            styles = {"wikilight": config.PLOT_STYLE, "table": config.TABLE_STYLE}
            selected_style = styles.get(style, style)

            with plt.style.context(selected_style):
                if not subplots:
                    ax = kwargs.get("ax")
                    if ax is None:
                        with plt.ion():
                            canvas, ax = plt.subplots()
                    else:
                        canvas = ax.figure
                    kwargs["ax"] = ax
                    result = func(data, *args, **kwargs)
                    returned = canvas, result
                else:
                    returned = func(data, *args, **kwargs)
                    canvas = returned.figure if isinstance(returned, PlotLayout) else returned[0]

                attrs = getattr(canvas, "attrs", {})
                if "NAME" not in attrs:
                    plot_name = func.__name__ if subplots else ax.get_title() or func.__name__
                    canvas.attrs = {**attrs, "NAME": plot_name}

                if plot_heading := title(data):
                    if not subplots:
                        ax.set_title(plot_heading, multialignment="left")
                    else:
                        heading = canvas.suptitle(
                            plot_heading, y=1, va="top", fontsize=12,
                            multialignment="left",
                        )
                        canvas.canvas.draw()
                        height = heading.get_window_extent().height
                        pad = 10 * canvas.dpi / 72
                        canvas.subplots_adjust(top=1 - (height + pad) / canvas.bbox.height)

                plots = data.p
                if isinstance(returned, PlotLayout):
                    plots._layout = returned
                plots._figure = canvas
                attrs = getattr(canvas, "attrs", {})
                canvas.attrs = {**data.attrs, **attrs, **metadata(data)}

        return wrapper

    return decorator


def subplot(func):
    @wraps(func)
    def wrapper(data, *args, axes=None, **kwargs):
        axes = data.p.axes if axes is None else axes
        for position, ax in enumerate(axes):
            func(data.iloc[position], *args, ax=ax, **kwargs)

    return wrapper


class _PlotAccessor(CachedAccessor):
    def __init__(self, data):
        if hasattr(self, "_data"):
            return
        self._data = data
        self._layout = None
        self._figure = None

    @property
    def data(self):
        return self._data

    @property
    def figure(self):
        # Every plotting namespace shares the state owned by .p.
        return self._data.p._figure

    @property
    def axes(self):
        layout = self._data.p._layout
        return None if layout is None else layout.axes


PlotAccessor = _accessor("p", _PlotAccessor)
