import html
import inspect
import os
import pprint
import random
import time
from numbers import Integral, Real
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import nbformat
import pandas as pd
import uncertainties
from IPython import get_ipython
from IPython.core.magic import needs_local_scope
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import HTML, Image, clear_output, display
from matplotlib.figure import Figure

from labdata import config
from labdata.load import resolve_path


HELP_IMAGES = [
    "https://i.pinimg.com/originals/08/df/6b/08df6b41d9ab3498618f7050da8234a7.jpg",
    "https://cdn05.zipify.com/RQZYw7dLmDEk4o6MjUoZpEqKAbE=/fit-in/3840x0/3ce46b1ccb124af29d7bc3744f975d5b/pot013-dec-blogs-61.jpeg",
    "https://cdn.britannica.com/86/166986-050-4CEFE5DE/cute-kitten-and-puppy-outdoors-in-grass.jpg",
    "https://www.shutterstock.com/image-photo/border-collie-dog-portrait-hiding-600nw-1933485896.jpg",
    "https://static.posters.cz/image/750/art-photo/cute-panda-bear-climbing-in-tree-i210472.jpg",
    "https://travel.eatsandretreats.com/wp-content/uploads/2019/02/shutterstock_1297984597.jpg",
    "https://zoos.media/wp-content/uploads/2021/05/nycticebuspygmaeuslori.jpg",
    "https://ultimatekilimanjaro.com/wp-content/uploads/2024/01/cuteanimals20.jpg",
]


class Print(pprint.PrettyPrinter):
    def __init__(self):
        super().__init__(sort_dicts=False)

    def format(self, obj, context, maxlevels, level):
        if isinstance(obj, np.ndarray):
            return f"Array(shape={obj.shape}, dtype={obj.dtype});", 1, 0
        if isinstance(obj, str) and os.path.isfile(obj):
            return os.path.dirname(obj) + "<br>" + os.path.basename(obj), 1, 0
        if isinstance(obj, uncertainties.UFloat):
            return f"{obj:.2e}", 1, 0
        if isinstance(obj, np.generic):
            obj = obj.item()
        if isinstance(obj, Integral) and not isinstance(obj, bool):
            return str(obj), 1, 0
        if isinstance(obj, Real) and not isinstance(obj, bool):
            return f"{obj:.4g}", 1, 0
        if callable(obj):
            return f"Function(name={obj.__name__});", 1, 0
        return super().format(obj, context, maxlevels, level)


def evaluate(line, local_ns):
    shell = get_ipython()
    namespace = shell.user_ns if local_ns is None else local_ns
    return eval(line, shell.user_ns, namespace)


@needs_local_scope
def view_magic(line, local_ns=None):
    from labdata.notebook.view import viewer
    from labdata.notebook.widget import ViewWidget

    if line.strip():
        viewer(evaluate(line.strip().strip(","), local_ns))
    else:
        ViewWidget()


def liveview_magic(line):
    from labdata.notebook.view import viewer

    if line.strip():
        raise TypeError("%liveview does not accept arguments")
    viewer([], live=True)


@needs_local_scope
def print_magic(line, local_ns=None):
    data = evaluate(line, local_ns)
    if isinstance(data, pd.DataFrame):
        paths = [
            column.split(config.SEPARATOR) if isinstance(column, str) else [column]
            for column in data.columns
        ]
        depth = max((len(path) for path in paths), default=1)
        data = data.transpose()
        if depth > 1:
            data.index = pd.MultiIndex.from_tuples([
                tuple(path + [""] * (depth - len(path)))
                for path in paths
            ])
        data = data.map(Print().pformat)
        data = data.style.set_properties(**{
            "text-align": "left",
            "white-space": "pre-wrap",
        })
        data = data.set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("border", "1px solid #37373D !important"),
                    ("font-weight", "normal"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("border", "1px solid #37373D !important"),
                    ("font-weight", "normal"),
                    ("min-width", "400px"),
                ],
            },
        ])
        display(HTML(data.to_html()))
    else:
        display(HTML(f"<pre>{html.escape(Print().pformat(data))}</pre>"))


@needs_local_scope
def help_magic(line, local_ns=None):
    obj = evaluate(line, local_ns) if line.strip() else None
    if obj is None:
        try:
            while True:
                clear_output(wait=True)
                display(Image(url=random.choice(HELP_IMAGES)))
                time.sleep(2)
        except KeyboardInterrupt:
            clear_output()
        return

    signature = inspect.signature(obj)
    source = inspect.getsourcefile(inspect.unwrap(obj))
    text = (
        f"Signature: {html.escape(str(signature))}<br>"
        f"Source: {html.escape(str(source))}"
    )
    display(HTML(text))


def save(obj=None, *, name=None, directory=None):
    """Save a figure or DataFrame, inferring its name from figure metadata."""
    if obj is None:
        obj = plt.gcf()

    if isinstance(obj, pd.DataFrame):
        files = [
            file
            for value in obj["FILE"].dropna()
            for file in (value if isinstance(value, list) else [value])
        ] if "FILE" in obj else []
        methods = obj["METHOD"].dropna().tolist() if "METHOD" in obj else []
        inferred_name = methods[-1] if methods else "labdata"
    else:
        attrs = getattr(obj, "attrs", {})
        files = attrs.get("FILE", ())
        inferred_name = attrs.get("NAME", "plot")
        methods = attrs.get("METHOD", ())
        if methods:
            inferred_name += f"_{methods[-1]}"

    prefix = ""
    if directory is None and files:
        files = [resolve_path(file, cache=False) for file in files]
        run_folder = Path(files[0]).parent
        directory = config.SAVE_DIRECTORY(files)
        prefix = f"{run_folder.name}_"
    directory = Path.cwd() if directory is None else Path(directory)

    if name is None:
        name = inferred_name
    elif name.startswith("_"):
        name = inferred_name + name
    name = prefix + name

    extension = ".png" if isinstance(obj, Figure) else ".pkl"
    path = directory / f"{name}{extension}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, Figure):
        obj.savefig(
            path,
            metadata={"label": str(path.parent)},
            bbox_inches="tight",
        )
    else:
        obj.to_pickle(path)
    return path


@magic_arguments()
@argument("obj", nargs="?")
@argument("--name", "-n")
@argument("--directory", "-d")
@needs_local_scope
def save_magic(line, local_ns=None):
    args = parse_argstring(save_magic, line)
    obj = evaluate(args.obj, local_ns) if args.obj else None
    path = save(
        obj,
        name=args.name,
        directory=args.directory,
    )
    kind = "Plot" if path.suffix == ".png" else "Data"
    link = html.escape(str(path), quote=True)
    display(HTML(f'{kind} saved to <a href="{link}">{link}</a>'))

    notebook = path.with_suffix(".ipynb")
    history = get_ipython().history_manager.get_range()
    cells = [
        nbformat.v4.new_code_cell(source=source)
        for _, _, source in history
    ]
    nbformat.write(nbformat.v4.new_notebook(cells=cells), notebook)
    link = html.escape(str(notebook), quote=True)
    display(HTML(f'Code saved to <a href="{link}">{link}</a>'))


def load_ipython_extension(ipython):
    ipython.register_magic_function(view_magic, "line", "view")
    ipython.register_magic_function(liveview_magic, "line", "liveview")
    ipython.register_magic_function(print_magic, "line", "print")
    ipython.register_magic_function(help_magic, "line", "help")
    ipython.register_magic_function(save_magic, "line", "save")
