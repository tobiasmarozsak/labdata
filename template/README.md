# LabData extension template

This directory is a reference scaffold, not a place to implement a real lab
extension.

Copy `template/` out of the `labdata` checkout and make the copy its own
repository before adding loaders, configuration, setup definitions, or
scientific methods.

For example:

```bash
cp -R template ../labdata-mylab
cd ../labdata-mylab
git init
nbstripout --install --attributes .gitattributes
```

The copied `.gitattributes` enables notebook output stripping, while the
command activates its Git filter in the new repository. Run the same command
after cloning the lab repository on another machine.

Recommended naming convention:

- Distribution: `labdata-<lab>` using hyphens, for example `labdata-mylab`.
- Import package: `<lab>` as a valid Python identifier, for example `mylab`.
- Entry-point name: the same short lab identifier, for example `mylab`.

As an example, for a lab named `mylab`, make these changes in the copied repository:

1. Rename the source directory `src/template/` to `src/mylab/`.
2. In `pyproject.toml`, change the distribution name:

   ```toml
   [project]
   name = "labdata-mylab"
   ```

3. In the same file, change both sides of the entry point while leaving the
   group name `labdata.lab` unchanged:

   ```toml
   [project.entry-points."labdata.lab"]
   mylab = "mylab"
   ```

   The left side is the installed entry-point identifier. The right side is
   the Python package imported from `src/mylab/`.

4. Change the package-data key to the renamed resources package:

   ```toml
   [tool.setuptools.package-data]
   "mylab.resources" = ["*"]
   ```

For a multiword lab name, use hyphens in the distribution and underscores in
the Python and entry-point names, for example `labdata-my-lab` and
`my_lab`.

Install the core `labdata` checkout before installing the copied lab package
in each environment. Otherwise, pip may resolve the unrelated package with
that name from a package index.

After installing the copied package alongside `labdata`, verify discovery with:

```bash
python -c "from labdata import config; print(config.extension().__name__)"
```

This should print the renamed import package, such as `mylab`. Only one package
registered in the `labdata.lab` group may be installed in an environment.

The empty package layout shows the intended responsibility boundaries:

```text
src/template/
    __init__.py
    config.py
    load.py
    methods/
    plots/
    resources/
    setup/
    tools/
```

- `config.py` contains runtime paths, preferences, and the loading backend.
- `load.py` or a replacement `load/` package owns file-format interpretation.
- `methods/` contains lab-specific registered analysis methods. Import each
  defining module from `methods/__init__.py` so loading the lab package runs its
  decorators and exposes the functions through `data.m`.
- `plots/` contains new lab- or analysis-specific plotting and visualisation
  functions. They may also be registered on the shared DataFrame `.p`
  namespace. Import each module containing registered plots from
  `plots/__init__.py`; loading the lab package then runs the decorators and
  makes the functions available through `data.p`.
- `setup/` describes physical apparatus, atoms, transitions, and calibrations.
- `tools/` contains reusable functions that remain specific to the lab package.
  If a tool could be useful across laboratories, open a merge request to add it
  to the shared `labdata` package.
- `resources/` contains packaged styles and other presentation assets.
- `__init__.py` exposes these modules and imports `methods` so registrations
  run when `labdata` discovers the extension.

`config.py` defines the lab-specific loading settings using safe local
placeholders for the required data folder and filename pattern. The field
separator and optional visual, viewer, title, and save settings are listed as
`None`, which explicitly means to inherit the corresponding core default.
`load.py` exposes the full primitive reader interface; every reader raises
`NotImplementedError` until the copied extension supplies its file-format
implementation.

Do not commit lab-specific changes to this template in the core repository.
