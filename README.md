# LabData

The package `labdata` provides shared loading, analysis, plotting, viewer, and
notebook infrastructure for laboratory data.

The exact file structure, data
location, apparatus setup, calibrations, and lab-specific methods belong in a
separately installed lab package that interfaces with `labdata` through its
extension contract. An empty template is included for setting up that lab
package.

More detailed reference material is available in the
[reference notes](docs/notes.md). Runnable demonstrations cover
[analysis](demos/demo1.ipynb), [image scans](demos/demo2.ipynb),
[live registration](demos/demo3.ipynb), and
[HDF5 loading backends](demos/demo4.ipynb).

## Installation

Clone this repository or your fork, then enter the checkout:

```bash
git clone https://github.com/tobiasmarozsak/labdata.git
cd labdata
```

Create and activate a virtual environment:

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install the core package in editable mode:

```bash
python -m pip install -e .
```

## Notebook output stripping

LabData includes `nbstripout` and both this repository and the lab-package
template include the required `.gitattributes`. Activate the Git filter once
after cloning this repository, and once after creating or cloning each lab
package repository:

```bash
nbstripout --install --attributes .gitattributes
```

The filter removes notebook outputs and execution counts from staged content
without changing the working notebooks. Git filter configuration is local to a
repository and therefore cannot be activated automatically by cloning it.

## Create a lab package

First, read the template [README](template/README.md) in full.

Copy the template outside the core checkout and initialize the copy as its own
repository:

```bash
cp -R template ../labdata-mylab
cd ../labdata-mylab
git init
```

Rename all template identifiers:

1. Change the distribution name `labdata-template` to `labdata-<lab>` in
   `pyproject.toml`, for example `labdata-mylab`.
2. Rename the import package directory `src/template/` to a short valid Python
   identifier such as `src/mylab/`.
3. Change the entry-point name and target to that same identifier.
4. Change the package-data key from `template.resources` to the renamed
   resources package, such as `mylab.resources`.

Keep the entry-point group itself as `labdata.lab`. For a package imported as
`mylab`, the registration is:

```toml
[project.entry-points."labdata.lab"]
mylab = "mylab"
```

The template depends on `labdata`; core never imports a particular lab package
directly. Install at most one package registered in the `labdata.lab` group in
an environment.

## Configure the lab package

Implement `src/<package>/config.py` with the laboratory's runtime settings:

```python
from pathlib import Path

from . import load


DATA_FOLDER = Path("/path/to/data")
DATA_FOLDER_ALIASES = ()
DATA_FILE_PATTERN = r"(?i).*\.h5$"
LOAD_BACKEND = load.backend
CACHE_FOLDER = Path("/path/to/cache")
```

- `DATA_FOLDER` is the local root containing experiment data.
- `DATA_FOLDER_ALIASES` maps historical or cross-platform roots onto the local
  data folder.
- `CACHE_FOLDER` stores local copies of data files. It defaults to the current
  directory and is created automatically when paths are resolved.
- `DATA_FILE_PATTERN` is a full-match regular expression for completed data
  filenames.
- `LOAD_BACKEND(open_file)` returns the primitive reader appropriate for that
  file's schema.

The template also lists optional settings such as `SEPARATOR`, viewer defaults,
styles, title generation, and save-directory selection. Leave an option as
`None` to inherit the core default.

## Implement file loading

The template's `load.py` contains the complete primitive reader interface. Its
placeholder functions raise `NotImplementedError`; replace them with the lab's
file-format interpretation:

```python
def list_var(file): ...
def list_img(file): ...
def load_var(file, name): ...
def load_img(file, name, roi=None): ...
def meta_file(file): ...
def meta_img(file, image): ...
```

The functions receive an already-open file. They should return ordinary names,
values, arrays, and dictionaries without adding pandas conversion or collection
loops. Preserve row-first ROI order, and include explicit source
identity such as `FILE` in file metadata.

For one schema, `backend(file)` may return the `load` module itself. For
multiple schemas, inspect each file and return the matching reader module;
unknown layouts should fail clearly.

Once these primitives are implemented, core automatically supplies path and
collection handling, progress, `list_file`, `load_file`, selective `load_data`,
DataFrame conversion, the ordinary viewer, and live-view loading.
The self-contained [loading-backend demo](demos/demo4.ipynb) shows a minimal
implementation with HDF5 unit metadata and a derived optical-density image.

## Add lab-specific functionality

The remaining template packages separate responsibilities:

- `setup/` contains physical apparatus, atoms, transitions, cameras,
  photodiodes, and calibration definitions.
- `tools/` contains reusable lab-side functions. If a tool could be useful
  across laboratories, open a merge request to add it to the shared `labdata`
  package.
- `methods/` contains lab-specific analyses registered on the shared `.m` (or custom)
  namespace. Import each module containing registered methods from
  `methods/__init__.py` so loading the lab package runs its decorators and
  exposes the functions through `.m`.
- `plots/` contains new lab- or analysis-specific plotting and visualisation
  functions. They may also be registered on the shared DataFrame `.p`
  namespace. Import each module containing registered plots from
  `plots/__init__.py`; loading the lab package then runs the decorators and
  makes the functions available through `.p`.
- `resources/` contains packaged Matplotlib styles, notebook CSS, Qt QSS, and
  other presentation assets. Point configuration overrides at these resources.
- `config.py` controls runtime behavior; it should not become a container for
  physical setup definitions or scientific algorithms.

Lab methods may call core numerical tools and record methods, then add
calibrated quantities or experiment-specific interpretation. Keep reusable,
lab-independent numerical operations in `labdata`.

## Install and verify the lab package

Install the core `labdata` checkout before installing a lab package in each
environment. The lab package declares `labdata` as a dependency; if core is
not already installed, pip may resolve the unrelated package with that name
from a package index.

Install core and the copied extension into the same environment:

```bash
cd /path/to/labdata
python -m pip install -e .

cd /path/to/labdata-mylab
python -m pip install -e .
```

Restart Python after installing or changing entry-point metadata, then verify
discovery:

```bash
python -c "from labdata import config; print(config.extension().__name__)"
```

Ordinary Python edits are visible immediately in an editable installation,
although already imported modules and registered methods may need a Python or
notebook restart. Re-run the editable install after changing dependencies,
entry points, package discovery, or package-data declarations.
