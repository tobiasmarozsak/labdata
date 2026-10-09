import errno
import re
import shutil
import warnings
from functools import wraps
from os import PathLike, fsdecode
from pathlib import Path, PureWindowsPath

import h5py
import numpy as np
import pandas as pd

from labdata import config
from labdata.progress import progress
from labdata.tools.mapping import unravel


def _cache_folder():
    folder = Path(config.CACHE_FOLDER)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def resolve_path(path, cache=None):
    """Resolve a data path, preferring an existing cached file by default."""
    value = fsdecode(path)
    try:
        folder = config.DATA_FOLDER
    except AttributeError:
        folder = None
    try:
        aliases = config.DATA_FOLDER_ALIASES
    except AttributeError:
        aliases = ()
    folder = None if folder is None else Path(folder)

    normalized = value.replace("\\", "/")
    for alias in aliases:
        prefix = fsdecode(alias).replace("\\", "/").rstrip("/")
        if normalized.casefold() == prefix.casefold():
            path = folder
            break
        elif normalized.casefold().startswith(f"{prefix.casefold()}/"):
            relative = normalized[len(prefix) + 1:]
            path = Path(folder, *relative.split("/"))
            break
    else:
        path = Path(value)
        if (
            folder is not None
            and not path.is_absolute()
            and not PureWindowsPath(value).is_absolute()
        ):
            path = folder / path

    try:
        relative = path.relative_to(folder)
    except (TypeError, ValueError):
        relative = Path(*path.resolve().parts[1:])
    cached = _cache_folder() / relative

    if cache is True:
        return cached
    if cache is None and cached.is_file():
        return cached
    return path


def relative_path(path):
    path = resolve_path(path, cache=False)
    try:
        return path.relative_to(Path(config.DATA_FOLDER)).as_posix()
    except (AttributeError, TypeError, ValueError):
        return str(path)


def open_file(path):
    source_path = resolve_path(path, cache=False)
    path = resolve_path(path)
    source = open(path, "rb")
    try:
        content = source.read()
    finally:
        try:
            source.close()
        except OSError as error:
            if error.errno != errno.EBADF:
                raise
    file = h5py.File.in_memory(content)
    file.source = relative_path(source_path)
    return file


def list_file(path, exc=None, cache=False):
    if isinstance(path, (list, tuple, np.ndarray)):
        files = sorted({
            file
            for item in path
            for file in list_file(item, exc=exc)
        })
    else:
        path = resolve_path(path, cache=False)
        if not path.is_dir():
            files = [relative_path(path)]
        else:
            pattern = re.compile(config.DATA_FILE_PATTERN)
            files = sorted(
                relative_path(item)
                for item in path.rglob("*")
                if item.is_file()
                and pattern.fullmatch(item.name)
            )

    excluded = (exc,) if isinstance(exc, str) else (() if exc is None else exc)
    files = [
        file
        for file in files
        if not any(item in Path(file).stem for item in excluded)
    ]

    if cache:
        for source in progress(files, desc="list_file"):
            destination = resolve_path(source, cache=True)
            if not destination.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(resolve_path(source, cache=False), destination)
    return files


def readfile(func):
    @wraps(func)
    def wrapper(source, *args, **kwargs):
        if isinstance(source, (str, bytes, PathLike)):
            with open_file(source) as opened:
                return func(opened, *args, **kwargs)
        return func(source, *args, **kwargs)

    return wrapper


def vectorize(func):
    @wraps(func)
    def wrapper(source, *args, **kwargs):
        if isinstance(source, (list, tuple, np.ndarray)):
            results = []
            failures = []
            for item in progress(source, desc=func.__name__):
                try:
                    results.append(func(item, *args, **kwargs))
                except Exception as error:
                    identity = getattr(item, "source", None)
                    if identity is None:
                        identity = getattr(item, "filename", None)
                    if identity is None:
                        identity = fsdecode(item) if isinstance(
                            item, (str, bytes, PathLike)
                        ) else repr(item)
                    failures.append((identity, error))
            if failures:
                details = "\n".join(
                    f"- {identity}: {type(error).__name__}: {error}"
                    for identity, error in failures
                )
                warnings.warn(
                    f"{func.__name__} skipped {len(failures)} of "
                    f"{len(source)} sources:\n{details}",
                    RuntimeWarning,
                    stacklevel=2,
                )
            return results
        return func(source, *args, **kwargs)

    return wrapper


def dataframe(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        return pd.DataFrame(data if isinstance(data, list) else [data])

    return wrapper


# These primitive footprints support both selective loading and the complete
# load_file assembly used by the viewer.
@vectorize
@readfile
def list_var(f):
    return config.LOAD_BACKEND(f).list_var(f)


@vectorize
@readfile
def list_img(f):
    return config.LOAD_BACKEND(f).list_img(f)


@vectorize
@readfile
def load_var(f, name):
    return config.LOAD_BACKEND(f).load_var(f, name)


@vectorize
@readfile
def load_img(f, name, roi=None):
    return config.LOAD_BACKEND(f).load_img(f, name, roi=roi)


@vectorize
@readfile
def meta_file(f):
    return config.LOAD_BACKEND(f).meta_file(f)


@vectorize
@readfile
def meta_img(f, img):
    return config.LOAD_BACKEND(f).meta_img(f, img)


@dataframe
@vectorize
@readfile
def load_file(f):
    data = meta_file(f)
    for name in list_img(f):
        data[name] = load_img(f, name)
    for name in list_var(f):
        data[name] = load_var(f, name)
    return unravel(data)


@dataframe
@vectorize
@readfile
def load_data(f, var=None, img=None, roi=None):
    data = meta_file(f)
    if img is not None:
        image = load_img(f, img, roi=roi)
        images = tuple(image.values()) if isinstance(image, dict) else (image,)
        if roi is None:
            rows, columns = images[0].shape
            roi = (0, rows, 0, columns)
        data["IMAGE"] = image
        data["MASK"] = np.logical_and.reduce([~np.isnan(item) for item in images])
        data["METADATA"] = {**meta_img(f, img), "ROI": roi}
    if isinstance(var, str):
        data[var] = load_var(f, var)
    elif isinstance(var, list):
        for item in var:
            data[item] = load_var(f, item)
    elif isinstance(var, dict):
        for key, name in var.items():
            data[key] = load_var(f, name)
    return unravel(data)
