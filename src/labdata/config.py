import os
from functools import cache
from importlib.metadata import entry_points
from pathlib import Path

from labdata import resources


def plot_title(data):
    lines = []
    files = [
        file
        for value in data["FILE"].dropna()
        for file in (value if isinstance(value, list) else [value])
    ] if "FILE" in data else []
    if files:
        folders = sorted({str(Path(file).parent) for file in files})
        label = "Folder" if len(folders) == 1 else "Folders"
        lines.append(rf"$\bf{{{label}}}$: " + ", ".join(folders))
    if "METHOD" in data and not data["METHOD"].dropna().empty:
        lines.append(r"$\bf{Method}$: " + str(data["METHOD"].dropna().iloc[-1]))
    return "\n".join(lines)


def save_directory(files):
    folders = [Path(file).parent for file in files]
    root = Path(os.path.commonpath(folders))
    return root.parent if root in folders else root


DEFAULTS = {
    "SEPARATOR": "//",
    "CACHE_FOLDER": Path(),
    "DEFAULT_IMAGE": "IMAGE",
    "DEFAULT_COLORBAR": (0, 1),
    "PLOT_STYLE": resources.PLOT_STYLE,
    "TABLE_STYLE": resources.TABLE_STYLE,
    "WIDGET_CSS": resources.WIDGET_CSS,
    "VIEW_QSS": resources.VIEW_QSS,
    "PLOT_TITLE": plot_title,
    "SAVE_DIRECTORY": save_directory,
}


@cache
def extension():
    items = list(entry_points(group="labdata.lab"))
    if len(items) > 1:
        names = ", ".join(item.name for item in items)
        raise RuntimeError(f"Multiple labdata.lab extensions are installed: {names}")
    return None if not items else items[0].load()


def setting(name):
    package = extension()
    if package is not None:
        try:
            value = getattr(package.config, name)
        except AttributeError:
            pass
        else:
            if value is not None:
                return value
    if name in DEFAULTS:
        return DEFAULTS[name]
    if package is None:
        raise AttributeError(f"No lab extension supplies setting {name!r}")
    raise AttributeError(f"Installed lab configuration has no setting {name!r}")


def __getattr__(name):
    return setting(name)


def __dir__():
    package = extension()
    settings = () if package is None else dir(package.config)
    return sorted(set(globals()) | set(DEFAULTS) | set(settings))
