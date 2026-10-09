import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from labdata.matplotlib import _display_scale
from labdata.plots.core import PlotLayout, figure, label, name, register, title


XLABEL = {"labelpad": 3, "fontsize": 10, "fontweight": "normal"}
YLABEL = {"labelpad": 3, "fontsize": 10, "fontweight": "normal", "rotation": 0, "ha": "right", "va": "center"}
XGROUP = {"labelpad": 6, "fontsize": 10, "fontweight": "bold"}
YGROUP = {"labelpad": 5, "fontsize": 10, "fontweight": "bold", "rotation": 0, "ha": "right", "va": "center"}
YLABEL_OUTER_PAD = 4
TITLE = {"fontsize": 12}
TITLEPAD = 14

def _display(data, field):
    if not is_numeric_dtype(data[field]):
        return label(field), 1
    values = data[field].dropna().to_numpy()
    magnitude = np.max(np.abs(values)) if len(values) else 0
    return _display_scale(field, magnitude)


def _format(data, field, value):
    if isinstance(value, str):
        return value
    if isinstance(value, (np.datetime64, pd.Timestamp)):
        return str(value)[11:19]
    if isinstance(value, (int, float, np.number)):
        _, scale = _display(data, field)
        return f"{value * scale:g}"
    return str(value)


def _levels(data, field):
    levels = data[[field]].drop_duplicates()
    levels = levels.sort_values(field, kind="stable")
    return levels[field].tolist()


def _cell_label(data, position, fields):
    if not isinstance(fields, (list, tuple)):
        return None
    return "\n".join(
        _format(data, field, data.iloc[position][field]) for field in fields
    )


def _order(data, positions, x=None, y=None):
    fields, ascending = [], []
    if isinstance(y, (list, tuple)):
        fields += list(y)
        ascending += [False] * len(y)
    if isinstance(x, (list, tuple)):
        fields += list(x)
        ascending += [True] * len(x)
    if not fields:
        return positions
    values = data.iloc[positions][fields].reset_index(drop=True)
    order = values.sort_values(fields, ascending=ascending, kind="stable").index
    return np.asarray(positions)[order]


def _field_label(data, fields):
    if isinstance(fields, str):
        return _display(data, fields)[0]
    if isinstance(fields, (list, tuple)):
        return ", ".join(_display(data, field)[0] for field in fields)
    return None


def _measure(figure, text, **kwargs):
    artist = figure.text(0, 0, text, **kwargs)
    figure.canvas.draw()
    bounds = artist.get_window_extent().size
    artist.remove()
    return bounds


def _spacing(data, figure, shape, size, pad, xlabels, ylabels, x, y, heading):
    rows, columns = shape
    width, height = size
    xstyle = XGROUP if isinstance(x, str) else XLABEL
    ystyle = YGROUP if isinstance(y, str) else YLABEL
    points = figure.dpi / 72

    above, below = np.zeros(rows + 1), np.zeros(rows + 1)
    left, right = np.zeros(columns + 1), np.zeros(columns + 1)
    xlabel_height = np.zeros(rows + 1)
    ylabel_width = np.zeros(columns + 1)

    for (row, column), label in xlabels.items():
        text_width, text_height = _measure(
            figure, label,
            fontsize=xstyle["fontsize"], fontweight=xstyle["fontweight"],
        )
        overflow = max(0, (text_width - width) / 2)
        right[column] = max(right[column], overflow)
        left[column + 1] = max(left[column + 1], overflow)
        xlabel_height[row + 1] = max(
            xlabel_height[row + 1], text_height + xstyle["labelpad"] * points
        )

    for (row, column), label in ylabels.items():
        text_width, text_height = _measure(
            figure, label,
            fontsize=ystyle["fontsize"], fontweight=ystyle["fontweight"],
        )
        overflow = max(0, (text_height - height) / 2)
        below[row] = max(below[row], overflow)
        above[row + 1] = max(above[row + 1], overflow)
        ylabel_width[column] = max(
            ylabel_width[column],
            text_width
            + ystyle["labelpad"] * points
            + (YLABEL_OUTER_PAD * points if column else 0),
        )

    row_gaps = pad + above + below + xlabel_height
    column_gaps = pad + left + right + ylabel_width

    if xlabel := _field_label(data, x):
        _, text_height = _measure(figure, xlabel, **TITLE)
        row_gaps[-1] += text_height + TITLEPAD * points
    if ylabel := _field_label(data, y):
        text_width, _ = _measure(figure, ylabel, rotation=90, **TITLE)
        column_gaps[0] += text_width + TITLEPAD * points
    if heading:
        _, text_height = _measure(figure, heading, **TITLE)
        row_gaps[0] += text_height + 10 * points

    return row_gaps, column_gaps


def _layout(data, x, y, ncols):
    size = len(data)
    if size == 0:
        raise ValueError("Cannot create a table from an empty DataFrame")

    ncols = max(1, int(ncols))
    cells = [None] * size
    xlabels = {}
    ylabels = {}

    x_group = isinstance(x, str)
    y_group = isinstance(y, str)

    if not x_group and not y_group:
        columns = min(size, ncols)
        rows = math.ceil(size / columns)
        positions = _order(data, np.arange(size), x=x, y=y)
        for offset, position in enumerate(positions):
            cell = divmod(offset, columns)
            cells[position] = cell
            xlabel = _cell_label(data, position, x)
            ylabel = _cell_label(data, position, y)
            if xlabel is not None:
                xlabels[cell] = xlabel
            elif x is None and y is None:
                xlabels[cell] = str(position)
            if ylabel is not None:
                ylabels[cell] = ylabel
        return cells, (rows, columns), xlabels, ylabels

    if x_group and not y_group:
        levels = _levels(data, x)
        columns = min(len(levels), ncols)
        counts = [int((data[x] == value).sum()) for value in levels]
        block_heights = [
            max(counts[start:start + columns]) for start in range(0, len(levels), columns)
        ]
        rows = sum(block_heights)
        offsets = np.cumsum([0, *block_heights[:-1]])
        for group, value in enumerate(levels):
            positions = np.flatnonzero((data[x] == value).to_numpy())
            positions = _order(data, positions, y=y)
            block, column = divmod(group, columns)
            for offset, position in enumerate(positions):
                cell = (int(offsets[block] + offset), column)
                cells[position] = cell
                ylabel = _cell_label(data, position, y)
                if ylabel is not None:
                    ylabels[cell] = ylabel
            xlabels[(int(offsets[block] + block_heights[block] - 1), column)] = _format(data, x, value)
        return cells, (rows, columns), xlabels, ylabels

    if not x_group and y_group:
        levels = list(reversed(_levels(data, y)))
        counts = [int((data[y] == value).sum()) for value in levels]
        columns = min(max(counts), ncols)
        block_heights = [math.ceil(count / columns) for count in counts]
        rows = sum(block_heights)
        offsets = np.cumsum([0, *block_heights[:-1]])
        for group, value in enumerate(levels):
            positions = np.flatnonzero((data[y] == value).to_numpy())
            positions = _order(data, positions, x=x)
            for offset, position in enumerate(positions):
                row, column = divmod(offset, columns)
                cell = (int(offsets[group] + row), column)
                cells[position] = cell
                xlabel = _cell_label(data, position, x)
                if xlabel is not None:
                    xlabels[cell] = xlabel
            ylabels[(int(offsets[group]), 0)] = _format(data, y, value)
        return cells, (rows, columns), xlabels, ylabels

    xlevels = _levels(data, x)
    ylevels = list(reversed(_levels(data, y)))
    columns = min(len(xlevels), ncols)
    blocks = math.ceil(len(xlevels) / columns)
    rows = blocks * len(ylevels)
    for position, (_, record) in enumerate(data.iterrows()):
        xindex = xlevels.index(record[x])
        yindex = ylevels.index(record[y])
        block, column = divmod(xindex, columns)
        cell = (block * len(ylevels) + yindex, column)
        cells[position] = cell
    for xindex, value in enumerate(xlevels):
        block, column = divmod(xindex, columns)
        xlabels[((block + 1) * len(ylevels) - 1, column)] = _format(data, x, value)
    for block in range(blocks):
        for yindex, value in enumerate(ylevels):
            ylabels[(block * len(ylevels) + yindex, 0)] = _format(data, y, value)
    return cells, (rows, columns), xlabels, ylabels


@register
@figure("table", subplots=True)
def table(data, x=None, y=None, z="IMAGE", ncols=10, width=75, height=None, pad=3, **kwargs):
    heading = title(data)
    cells, (rows, columns), xlabels, ylabels = _layout(data, x, y, ncols)
    if height is None:
        if z in data:
            aspects = [np.asarray(value).shape[:2] for value in data[z]]
            height = width * np.median([shape[0] / shape[1] for shape in aspects])
        else:
            height = width

    dpi = kwargs.pop("dpi", plt.rcParams["figure.dpi"])
    with plt.ion():
        canvas = plt.figure(figsize=(1, 1), dpi=dpi, **kwargs)

    row_gaps, column_gaps = _spacing(
        data, canvas, (rows, columns), (width, height), pad,
        xlabels, ylabels, x, y, heading,
    )
    figure_width = columns * width + column_gaps.sum()
    figure_height = rows * height + row_gaps.sum()
    canvas.set_size_inches(figure_width / dpi, figure_height / dpi)

    xpositions = np.cumsum(np.r_[
        column_gaps[0], np.full(columns - 1, width) + column_gaps[1:-1]
    ])
    ypositions = figure_height - np.cumsum(np.r_[
        row_gaps[0] + height, np.full(rows - 1, height) + row_gaps[1:-1]
    ])

    frames = np.empty((rows, columns), dtype=object)
    for row in range(rows):
        for column in range(columns):
            position = (
                xpositions[column] / figure_width, ypositions[row] / figure_height,
                width / figure_width, height / figure_height,
            )
            ax = canvas.add_axes(position)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.patch.set_alpha(0)
            for spine in ax.spines.values():
                spine.set_color("0.5")
                spine.set_alpha(0.5)
            frames[row, column] = ax

    for cell, ax in np.ndenumerate(frames):
        if cell in xlabels:
            ax.set_xlabel(xlabels[cell], **(XGROUP if isinstance(x, str) else XLABEL))
        if cell in ylabels:
            ax.set_ylabel(ylabels[cell], **(YGROUP if isinstance(y, str) else YLABEL))

    grid_left, grid_right = xpositions[0], xpositions[-1] + width
    grid_top, grid_bottom = ypositions[0] + height, ypositions[-1]
    if xlabel := _field_label(data, x):
        canvas.text(
            (grid_left + grid_right) / (2 * figure_width), pad / figure_height,
            xlabel, ha="center", va="bottom", **TITLE,
        )
    if ylabel := _field_label(data, y):
        title_width, _ = _measure(canvas, ylabel, rotation=90, **TITLE)
        canvas.text(
            (pad + title_width / 2) / figure_width,
            (grid_bottom + grid_top) / (2 * figure_height), ylabel,
            rotation=90, ha="center", va="center", rotation_mode="anchor", **TITLE,
        )

    plot_name = "table"
    if isinstance(x, str):
        plot_name += f"_{name(x)}"
    if isinstance(y, str):
        plot_name += f"_{'and_' if isinstance(x, str) else ''}{name(y)}"
    canvas.attrs = {"NAME": plot_name}
    return PlotLayout(canvas, tuple(frames[cell] for cell in cells))
