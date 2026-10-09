import math
import re

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from labdata import config


XLABEL = plt.Axes.set_xlabel
YLABEL = plt.Axes.set_ylabel
PREFIX = {-12: "p", -9: "n", -6: "µ", -3: "m", 0: "", 3: "k", 6: "M", 9: "G", 12: "T"}
FACTOR = {prefix: 10**power for power, prefix in PREFIX.items()} | {
    "u": 1e-6, "c": 1e-2, "d": 1e-1, "da": 1e1, "h": 1e2,
}
BASE = "m s g A K mol cd Hz N Pa J W C V F Ω S Wb T G H Bq Gy Sv kat".split()
UNITS = {
    prefix + base: (factor, base, True)
    for base in BASE
    for prefix, factor in FACTOR.items()
}
UNIT = re.compile(r"(.*)\[([^]]+)]$")


def _display_scale(field, magnitude):
    text = str(field)
    match = UNIT.fullmatch(text)
    if match:
        name, unit = match.groups()
        factor, unit, si = UNITS.get(unit, (1, unit, False))
        dimensionless = False
    else:
        name, unit, factor, si = text, "", 1, False
        dimensionless = True

    magnitude = abs(magnitude) * factor
    power = (
        3 * math.floor(math.log10(magnitude) / 3)
        if magnitude and math.isfinite(magnitude)
        else 0
    )
    if dimensionless and 1e-3 <= magnitude < 1e3:
        power = 0

    name = name.split(config.SEPARATOR)[-1].strip()
    if dimensionless:
        label = name + (f" [×1e{power}]" if power else "")
    elif si:
        power = min(12, max(-12, power))
        label = f"{name} [{PREFIX[power]}{unit}]"
    else:
        unit = (f"×1e{power} " if power else "") + unit
        label = f"{name} [{unit}]"
    return label, factor / 10**power


def format_value(field, value):
    nominal = value.n if hasattr(value, "n") else value
    label, scale = _display_scale(field, nominal)
    value = value * scale
    text = f"{value:.2uP}" if hasattr(value, "n") else f"{value:.3g}"
    return label, text


def _minor_labels(axis):
    lower, upper = sorted(axis.get_view_interval())
    major = [value for value in axis.get_majorticklocs() if lower <= value <= upper]
    missing = 2 - len(major)
    if missing <= 0:
        return ()

    minor = [value for value in axis.get_minorticklocs() if lower <= value <= upper]
    if missing == 1 and minor:
        return (max(minor, key=lambda value: min(abs(value - tick) for tick in major)),)
    return tuple(minor[::max(1, len(minor) - 1)][:missing])


def update(ax, direction):
    state = getattr(ax, f"_labdata_{direction}")
    limits = getattr(ax, f"get_{direction}lim")()
    magnitude = max(abs(limits[0]), abs(limits[1]))
    label, scale = _display_scale(state["field"], magnitude)
    formatter = FuncFormatter(lambda value, position: f"{value * scale:.4g}")
    axis = getattr(ax, f"{direction}axis")
    axis.set_major_formatter(formatter)
    axis.set_minor_formatter(FuncFormatter(
        lambda value, position: (
            f"{value * scale:.4g}" if value in _minor_labels(axis) else ""
        )
    ))
    state["label"](ax, label, *state["args"], **state["kwargs"])


def setlabel(ax, label, direction, original, args, kwargs):
    text = str(label) if label is not None else ""
    match = UNIT.fullmatch(text)
    name = f"_labdata_{direction}"
    axis = getattr(ax, f"{direction}axis")

    if not text.strip() or (not match and axis.get_converter() is not None):
        if hasattr(ax, name):
            state = getattr(ax, name)
            ax.callbacks.disconnect(state["callback"])
            axis.set_major_formatter(state["major"])
            axis.set_minor_formatter(state["minor"])
            delattr(ax, name)
        return original(ax, label, *args, **kwargs)

    if not hasattr(ax, name):
        state = {"major": axis.get_major_formatter(), "minor": axis.get_minor_formatter()}
        state["callback"] = ax.callbacks.connect(
            f"{direction}lim_changed", lambda axes: update(axes, direction)
        )
        setattr(ax, name, state)

    state = getattr(ax, name)
    state.update(field=text, label=original, args=args, kwargs=kwargs)
    update(ax, direction)
    return axis.label


def xlabel(ax, label, *args, **kwargs):
    return setlabel(ax, label, "x", XLABEL, args, kwargs)


def ylabel(ax, label, *args, **kwargs):
    return setlabel(ax, label, "y", YLABEL, args, kwargs)


plt.Axes.set_xlabel = xlabel
plt.Axes.set_ylabel = ylabel
