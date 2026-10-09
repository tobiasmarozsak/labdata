# labdata reference

- `labdata` loads, analyses, and plots laboratory data using ordinary nested
  dictionaries, pandas DataFrames, NumPy arrays, and Matplotlib objects.
- The core package provides reusable data handling and numerical tools.
- A separately installed lab extension provides file-format knowledge, paths,
  setup information, calibrations, and lab-specific methods.
- Runnable examples are available in the
  [demo notebooks](../demos/), which are the best place to start.

## Matplotlib labels and units

- Importing `labdata` activates a narrow global Matplotlib label patch.
  - Automatically applies through ordinary `ax.set_xlabel(...)`,
    `ax.set_ylabel(...)`, `plt.xlabel(...)`, and `plt.ylabel(...)` calls.
  - Reads units from field labels such as `time[s]` or `position[m]`.
  - Assumes the numerical data are already stored in the stated unit.
  - Chooses an engineering-scale display from the visible axis range.
  - Example: values stored in seconds may be displayed with millisecond ticks
    and the label `time [ms]`.
  - Recalculates the displayed prefix and tick values after zooming or changing
    the axis limits.
  - Changes only tick formatting and the displayed label; plotted data and
    artist coordinates are not modified.
  - Plot limits and other numerical arguments therefore remain in the stored
    unit.
  - Removes parent field paths from labels: `scan//time[s]` displays as
    `time [...]`.
  - Uses SI prefixes for recognised simple units.
  - Uses an explicit `×1e...` scale for other units and dimensionless values.
  - Leaves categorical, datetime, and other Matplotlib-converted axes alone
    when the supplied label does not specify a unit.
  - Works with other axis scales, including logarithmic scales.

## DataFrames and nested records

- Importing `labdata` activates a narrow pandas patch.
  - Does not introduce a custom DataFrame or record class.
  - Automatically flattens nested dictionaries passed to `pd.DataFrame(...)`.
  - Represents nested paths as real columns joined with `config.SEPARATOR`,
    which defaults to `//`.
  - Example: `{"fit": {"centre[m]": 0.002}}` becomes the column `fit//centre[m]`.
  - Only mappings are flattened; arrays, lists, tuples, paths, and other values
    remain ordinary leaf values.
  - Nested dictionary keys must not contain the configured separator because it
    is reserved for field paths.
  - Keeps ordinary exact column lookup as the first choice.
  - If no exact column named `fit` exists, `df["fit"]` selects all `fit//...`
    columns, removes the prefix, and returns a DataFrame containing that subtree.
  - Example: `df["fit"]` may return a DataFrame with columns `centre[m]`,
    `sigma[m]`, and `rsqr`.
  - Preserves the original DataFrame index during subtree selection.
  - Field lookup is exact; there is no fuzzy or unit-insensitive matching.
  - Does not patch assignment, grouping, sorting, merging, or other normal
    pandas operations.
  - Importing the package also registers DataFrame accessors:
    - `df.m`: scientific methods that transform, measure, or fit records.
    - `df.p`: the default namespace for plotting methods that use DataFrame
      fields directly.
    - Custom namespaces can contain methods, plots, or both.
    - These accessors organise functions without adding them to the main pandas
      API or creating a DataFrame subclass.
    - Scientific values and source information remain ordinary DataFrame
      columns; the accessors do not contain hidden scientific data.
    - The following sections describe the registered methods in more detail.

## Notebook commands

- Load explicitly with `%load_ext labdata.notebook`. Importing the package alone does not register notebook magics.
- `%view DATA`:
  - Opens the interactive viewer for a DataFrame, record, image, file path, directory, or collection of files.
  - Evaluates `DATA` as an ordinary Python expression from the notebook.
- `%view` without an argument:
  - Displays a small notebook widget listing recent experiment folders.
  - Provides a quick way to find data files and open them in the interactive viewer.
- `%liveview`:
  - Opens the viewer in live mode.
  - Reacts only to filesystem move/rename events whose destination filename matches the configured data-file pattern.
  - The experiment should create and populate each file under a temporary extension, such as `.tmp`.
  - After closing the file and completing all writes, the experiment should rename it to its final `.h5` or `.hdf5` filename, signalling that the file is ready to open.
- `%print DATA`:
  - Displays compact, readable details without changing `DATA`.
  - DataFrames are displayed with nested, hierarchical field labels.
  - Uses compact formatting for numbers, arrays, functions, and other values.
- `%help FUNCTION`:
  - Shows the callable signature and source-file path.
  - Follows decorated functions back to their original implementation.
  - Without an argument, displays an image slideshow.
- `%save`:
  - Saves the current Matplotlib figure as PNG.
  - Saves the notebook input history beside it as an `.ipynb` file.
  - The file name and location are inferred from `FILE`, `METHOD`, and figure
    metadata.
- `%save DATA`:
  - Saves a DataFrame as a pickle file.
  - Also saves the notebook input history beside it.
- `%save FIGURE`:
  - Saves an explicitly selected Matplotlib figure instead of the current figure.
- `%save -n NAME` or `%save DATA -n NAME`:
  - Overrides the inferred output name.
  - A name beginning with `_` is appended to the inferred name instead of
    replacing it.
- `%save -d DIRECTORY`:
  - Overrides the inferred output directory.
- In most cases `%save` needs no arguments because names and locations are
  inferred from `FILE`, `METHOD`, and figure metadata.

## Interactive viewer

- Opens as a native Qt window through `%view DATA`.
- Accepts a DataFrame, dictionary, 2D NumPy array, file path, directory, or collection (list) of these.
- Treats each DataFrame row or source file as one navigable item.
- Recursively discovers matching data files when given a directory.
- Uses the core `load_file` interface for file contents.
- Defers opening a file until that item is selected.
- Previous/Next buttons and the left/right arrow keys move between items.
- The index selector jumps directly to a particular item.
- The image selector switches between all 2D arrays in the selected item.
- Initially prefers the image name/type configured by `DEFAULT_IMAGE` when it is available.
- Displays non-image fields in the table beside the image.
- Shows horizontal and vertical image profiles beside the main image.
- ROI mode:
  - Enables a movable and resizable rectangular region.
  - Uses ROI order `(row_start, row_stop, column_start, column_stop)`.
  - Profiles are summed across the active ROI when the crosshair is disabled.
  - Can be toggled with the down-arrow shortcut.
- Crosshair mode:
  - Enables movable horizontal and vertical sampling lines.
  - Profiles show the selected image row and column.
  - Can be toggled with the up-arrow shortcut.
- Colour controls:
  - The histogram/colorbar can be adjusted interactively.
  - Numerical colour limits can be entered directly.
  - Automatic levels can be enabled for newly displayed images.
  - Initial limits come from `DEFAULT_COLORBAR`.
- Pressing Escape closes the viewer.
- Live viewer:
  - Uses the same controls and display as the ordinary viewer.
  - Uses a filesystem watcher and displays files from the last completed
    file's directory.

## DataFrame plotting

- Core plotting functions use the DataFrame `.p` accessor by default.
- Example: `data.p.plot(x="time[s]", y="position[m]")`.
- Plot functions can instead be registered on any accessor, including one
  that also contains analysis methods.
- Regardless of the namespace used to call a plot, `.p` owns the current
  figure and row-to-axis layout as `data.p.figure` and `data.p.axes`.
- Does not replace pandas' built-in `data.plot` accessor.
- Uses ordinary DataFrame columns as plotting fields.
- Produces ordinary Matplotlib figures, axes, and artists.
- Accepts familiar Matplotlib keyword arguments such as `marker`, `color`,
  `cmap`, `vmin`, `vmax`, `alpha`, and `ax` where applicable.
- An explicit `ax=` can be supplied to compose plots in an existing figure.
- Automatically uses field names for labels, including the Matplotlib unit formatting described above.
- Applies project plotting styles locally; it does not permanently change the
  user's global Matplotlib style.
- Stores `FILE`, `METHOD`, and the plot name on the figure so `%save` can
  infer its name and location.
- Built-in implementations live in `src/labdata/plots/` and are registered on
  `.p` when the package is imported.
- Scalar/collection plotting methods:
  - `.p.plot(...)`: line plots, optionally grouped by a third field `z`.
  - `.p.scatter(...)`: scatter plots; `z` can colour a two-dimensional scan.
  - `.p.errorbar(...)`: groups repeated measurements and plots their mean and standard deviation.
  - `.p.hist(...)`: histogram with count, mean, standard deviation, and a highlighted one-standard-deviation interval.
  - `.p.pcolormesh(...)`: converts a two-parameter scan into a coloured grid.
  - `.p.twinplot(...)`: plots two dependent fields against one shared x field using left and right y axes.
  - `.p.pairplot(...)`: creates a Seaborn pair plot for selected fields.
  - `.p.fit(...)`: fits scalar x/y fields across the collection and overlays the fitted curve and parameter summary.
- Image collection plotting uses a layout followed by one or more renderers:
  - `.p.table(...)`: creates and stores a grid mapping each DataFrame row to one Matplotlib axis.
  - `x` and `y` fields control sequential, grouped, two-dimensional, and wrapped table layouts.
  - `.p.imshow(...)`: draws one image field into each stored table axis.
  - `.p.crosshair(...)`: overlays crosshair lines on each stored table axis.
  - `.p.implot(...)`: draws per-record image slices, summed profiles, radial profiles, masks, and optional existing fit overlays.
  - Renderers can be layered by calling them sequentially after `.p.table()`.
  - The current table figure and row-to-axis mapping are available as `data.p.figure` and `data.p.axes`.

## DataFrame methods

- Analysis operations are exposed through the DataFrame `.m` accessor.
- Example: `cropped = data.m.imagecrop(roi=(10, 80, 20, 100))`.
- Methods return new data, allowing pipelines such as
  `data.m.imagecrop(...).m.imagenorm(...).m.gauss2dfit()`.
- Each DataFrame row is converted into an ordinary nested dictionary before the scientific function runs.
- Flattened fields such as `var//sigma[pixel]` therefore appear inside a method as `record["var"]["sigma[pixel]"]`.
- Returned record dictionaries are converted back into ordinary flattened DataFrames.
- This conversion boundary keeps the scientific functions simple:
  - A method is an ordinary Python function operating on a nested dictionary
    or a list of nested dictionaries.
  - The function does not need to understand the pandas framework.
- Input records are not mutated:
  - Mapping containers are copied recursively.
  - Existing NumPy arrays are exposed to the method as read-only views.
  - The caller's original arrays remain unchanged and keep their original writeability.
  - A method that changes an array should calculate and assign a new array rather than modifying it in place.
- `METHOD` is an ordinary column set automatically and used by plot headings and `%save`.
- Per-record methods run independently for each DataFrame row.
- If one record fails, it is omitted while the remaining records continue; one
  warning reports all failures after progress finishes.
- A method called with a single record still raises its error normally.
- Collection methods receive all records together when the calculation depends on the collection as a whole.
- Core methods use only information already contained in the records.
- Lab extensions can register calibration- or setup-aware methods on the same
  `.m` namespace.
- A lab can deliberately replace a same-named core method; replacement prints
  a concise notice.
- Core image preparation methods:
  - `.m.imagecrop(...)`: crops `IMAGE` and `MASK` and updates the row-first source ROI.
  - `.m.imagenorm(...)`: subtracts a reference level selected from a region, excluded region, border, or the whole-image median.
  - `.m.imagemask(...)`: combines the existing mask with lower/upper image thresholds and optional smoothing.
  - `.m.imagerotate(...)`: rotates the image and mask into a new image frame.
  - `.m.imagemean(...)`: averages the whole collection or groups selected by an exact field.
- Core measurement and decomposition methods:
  - `.m.pixelsum(...)`: calculates signal sum, centre, and widths in pixels.
  - `.m.fft(...)`: calculates a per-record 2D Fourier transform and inverse-pixel frequency axes.
  - `.m.pca(...)`: calculates shared image modes and per-record coefficients across a collection.
- Core per-record image fits:
  - `.m.gauss1dfit(...)` and `.m.gauss2dfit(...)`.
  - `.m.bec1dfit(...)` and `.m.bec2dfit(...)`.
  - `.m.becthermal1dfit(...)` and `.m.becthermal2dfit(...)`.
  - Fit centres include the source ROI offset.
  - Core fit positions and widths are reported in pixels; physical calibration belongs to a lab method.
  - `.m` fits each image record independently; `.p.fit(...)` instead fits scalar fields across a collection and draws the result.
- Custom methods and plots:
  - `method` and `register` are imported together: `from labdata.methods import method, register`.
  - Registration is dynamic: defining a decorated function adds it to the framework immediately in the current Python session.
  - Existing DataFrames can use a newly registered method immediately; they
    do not need to be recreated.
  - Methods can be defined, tested, and revised interactively in a notebook.
  - The same mechanism also supports methods defined in ordinary Python modules and lab extensions.
  - `@method(vectorise=True)` supplies copying and per-record execution.
  - `@method()` supplies copying while calling the function once with the complete collection.
  - `@register` exposes the function on `.m` by default.
  - `@register(accessor="custom")` creates or uses a separate namespace, exposing the function as `data.custom.function(...)`.
  - Plot functions use the `register` exported by `labdata.plots`; bare
    `@register` uses `.p`, while `@register(accessor="custom")` places the plot
    on another namespace.
  - Method and plot functions may share a custom namespace, for example
    `data.lattice.visibility(...)` and `data.lattice.visibility_rois()`.
  - `@figure` defines standalone plots, while `@subplot` pairs one-record renderers with the row-aligned axes created by `.p.table(...)`.
  - All plotting namespaces share the layout created on `.p`, so custom renderers can use the row-aligned axes from `.p.table(...)`.
  - Custom method functions remain ordinary Python functions and can also be called directly with dictionaries or lists of dictionaries.
  - Registering the same name again replaces the previous implementation and
    prints a concise notice.

## Loading experimental data

- Loading is split between reusable core features and lab-specific file interpretation.
- Core handles paths, file opening, collections, progress, DataFrame conversion, and complete-record assembly.
- The installed lab extension defines what variables, images, and metadata
  mean inside a file.
- Core does not import a particular lab package directly.
- The lab exposes a `LOAD_BACKEND` dispatcher through its configuration.
- The dispatcher can inspect each open file and choose the appropriate schema reader independently.
- Mixed collections can therefore contain files from multiple schema versions supported by the same lab.
- File discovery with `list_file(...)`:
  - Accepts a file, directory, or collection of paths.
  - Searches directories recursively.
  - Includes filenames matching the lab's configured `DATA_FILE_PATTERN`.
  - `exc=` excludes files whose stem contains one of the supplied strings.
  - Returns paths in sorted order without opening the experiment files.
  - Paths below the configured `DATA_FOLDER` are stored as portable relative POSIX paths.
  - Configured path aliases can map historical paths from another machine or
    operating system onto the local data folder.
  - `cache=False` is the default and performs no file copying.
  - `cache=True` copies files that are missing from the local analysis cache.
  - `config.CACHE_FOLDER` selects the local cache directory. It defaults to
    the current directory and is created automatically.
  - The returned source paths remain unchanged; later reads automatically prefer an existing cached copy.
  - Existing cached files are not refreshed automatically.
- File opening with `open_file(...)`:
  - Resolves aliases, relative paths, and an existing local cache before opening.
  - Reads the complete physical file into memory, then opens it as an in-memory HDF5 file.
  - Avoids leaving the original filesystem or network-share descriptor attached to HDF5.
  - Adds the portable source identity as `file.source`.
  - Returned handles should be used with a `with` block and closed after use.
- Primitive loading functions:
  - `list_var(file)`: lists the variable names advertised by the lab reader.
  - `list_img(file)`: lists the image names advertised by the lab reader.
  - `load_var(file, name)`: loads one exact variable value.
  - `load_img(file, name, roi=None)`: loads one image, optionally cropped using
    row-first ROI order.
  - `meta_file(file)`: loads source-level metadata such as `FILE`, time, and iteration information.
  - `meta_img(file, image)`: loads metadata associated with an image or camera.
  - These functions accept a path, an already-open file, or a collection.
  - Caller-owned open files are not closed by the core wrappers.
- Complete loading with `load_file(...)`:
  - Loads source metadata, every advertised image, and every advertised variable.
  - Returns an ordinary DataFrame, one row per file.
  - This is the single content-loading interface used by the ordinary and live viewers.
  - It can be expensive because every image is decoded for the selected file.
- Selective loading with `load_data(...)`:
  - Loads only the variables and image requested for an analysis workflow.
  - Example: `load_data(files, var=["tof[s]"], img="CAM//OD", roi=ROI)`.
  - `var` can be one field name, a list of names, or a mapping from output
    names to source names.
  - A selected image is stored under `IMAGE`.
  - `MASK` marks pixels that are finite across all returned image arrays.
  - `METADATA` combines lab image metadata with the effective row-first `ROI`.
  - Returns an ordinary DataFrame, one row per file.
- Collection loading:
  - Lists, tuples, and NumPy arrays of sources are processed in source order.
  - If one file fails, that file is skipped and the remaining files continue loading.
  - Failed files are omitted completely; no empty, unchanged, or partially loaded row is returned.
  - After progress finishes, one warning lists every failed source and its error.
  - A single-file call still raises its error normally.
- Lab backend primitives receive an already-open HDF5 handle and implement
  `list_var`, `list_img`, `load_var`, `load_img`, `meta_file`, and `meta_img`
  directly.
- The core public loading functions apply `@readfile`, `@vectorize`, and
  `@dataframe` where needed; lab backend primitives do not need these
  decorators.

## Progress bars

- Shared by collection loading and vectorised DataFrame methods.
- Enabled by default for user-facing collection operations.
- Only the outermost operation displays a bar, preventing nested loaders or
  methods from producing duplicate bars.
- Disable progress temporarily with a context:
  ```python
  with labdata.progressbar(False):
      result = data.m.gauss2dfit()
  ```
- The previous setting is restored automatically after leaving the context.
- The setting is context-local, so a temporary choice does not become global
  state.
- Progress belongs to execution; methods and loaders do not reserve a `progress=` keyword argument.

## Numerical tools

- Reusable numerical building blocks live in `labdata.tools`.
- Tools are ordinary functions operating on arrays and mappings.
- They do not depend on DataFrames, record field names, file formats, lab
  configuration, or plotting state.
- They do not interpret experimental metadata or apply physical calibrations.
- Units are not inferred: input and output numbers retain the units implied by the caller.
- `.m` methods use these tools and add record handling, masks, ROI offsets,
  method information, and field names around them.
- Tools can also be imported and called directly when only the numerical operation is needed.
- Example:
  ```python
  from labdata import tools
  from labdata.tools import fit1

  cropped = tools.crop(image, ROI)
  result = fit1.gaussian(x, y)
  ```
- Image tools:
  - `inversion_centre(image)`: estimates the centre from inversion symmetry.
  - `clip_roi(image, roi)`: clips a row-first ROI to the image bounds.
  - `centre_roi(image, size, centre=None)`: constructs a centred, clipped ROI.
  - `crop(image, roi)`: returns a read-only cropped view.
  - `normalize(image, edge=5)`: subtracts the mean image-border value.
  - `rotate(image, angle, centre=None, **kwargs)`: rotates around a selected or
    estimated centre while preserving shape.
- Fourier tools:
  - `fft(image)`: centred, orthonormal two-dimensional Fourier transform.
  - `ifft(image)`: centred, orthonormal inverse transform.
  - `resize(image, sub=None, sup=None)`: Fourier-based resampling by cropping
    or padding frequency space.
- PCA tool:
  - `pca(images, num=None, sigma=2)`: performs image-stack decomposition with
    optional Gaussian smoothing.
  - Returns mode images, singular values, and per-image coefficients in an
    ordinary dictionary.
- Mapping tools:
  - `ravel(mapping)`: flattens nested dictionary paths using the configured separator.
  - `unravel(mapping)`: reconstructs nested dictionaries from configured flat paths.
  - These are the same conversions used at the DataFrame/method boundary.
- Numerical fitting foundation:
  - `lsfit(x, y, fun, p0, **kwargs)` is the shared least-squares fitting engine
    built on `lmfit`.
  - Inputs are converted to NumPy arrays before fitting and guess logic.
  - Values carrying uncertainties use inverse-standard-deviation weights by default.
  - Ordinary numeric values retain unit weight.
  - Explicit `weights=` override the automatic weights.
  - Non-finite coordinates, observations, and weights are excluded from the
    fit.
  - Initial parameters are passed with `p0=` using the model's parameter names.
  - A plain value is shorthand for an unconstrained starting value: `"offset": 0.0`.
  - A parameter-options dictionary can specify:
    - `value`: starting value.
    - `min` and `max`: lower and upper bounds.
    - `vary=False`: keep the parameter fixed.
    - `expr`: constrain the parameter using an expression involving other
      parameters.
    - Other options accepted by `lmfit.create_params`.
  - Example:
    ```python
    p0 = {
        "centre": {"value": 0.0, "min": -1.0, "max": 1.0},
        "sigma": {"value": 0.2, "min": 0.0},
        "height": 1.0,
        "offset": {"value": 0.0, "vary": False},
    }
    result = fit1.gaussian(x, y, p0=p0)
    ```
  - Supplying `p0` replaces the model's automatic guess; normally include
    every required model parameter.
  - An existing `lmfit.Parameters` object can also be passed directly as
    `p0`.
  - The result includes fit status, fitted parameters, uncertainties,
    covariance, residuals, weights, best-fit values, and the underlying
    `lmfit` model result.
- One-dimensional fit models live in `labdata.tools.fit1`:
  - Operate on numerical `x` and `y` arrays.
  - Include linear, exponential, multi-exponential, Gaussian, Lorentzian,
    parabola, hyperbola, sinusoid, damped sinusoid, beat sinusoid,
    error-function, and power-law fits.
  - Each fit supplies a model function and an automatic initial-guess function.
  - A caller can provide `p0` to replace the automatic guess.
- Image fit models live in `labdata.tools.fit2`:
  - Operate directly on numerical image arrays.
  - Include Gaussian, BEC, and BEC-plus-thermal fits using one-dimensional
    projections or full two-dimensional models.
  - Return the numerical fit payload together with derived `var` and
    uncertainty-valued `uvar` dictionaries.
  - Centres are local image coordinates at this level; `.m` wrappers add
    record ROI offsets.
- Expensive deterministic fit functions use the shared in-memory cache:
  - Equivalent inputs reuse cached results.
  - Array keys include complete contents, shape, and dtype.
  - Cached results are copied on storage and return so callers cannot corrupt later results.

## Lab extensions

- The core package works without a lab extension for already-loaded data,
  methods, numerical tools, and plotting.
- A lab extension is a separate Python package containing local file-format
  knowledge, data paths, setup definitions, calibrations, methods, plots, and
  presentation resources.
- The extension depends on `labdata`; the core package never imports a
  particular lab package directly.
- Extensions register through the `labdata.lab` entry-point group.
- Install at most one lab extension in an environment.
- Extension discovery is lazy and is triggered when an extension-backed
  configuration value is first requested.
- Configuration is accessed through ordinary attributes such as
  `config.DATA_FOLDER` and `config.DEFAULT_IMAGE`.
- A non-`None` extension setting overrides the corresponding core default.
- Missing or `None` values use the core default when one exists.
- Lab-specific settings without a value raise `AttributeError`.
- A lab extension normally supplies `DATA_FOLDER`, `DATA_FILE_PATTERN`, and
  `LOAD_BACKEND`; it may also supply path aliases, viewer defaults, styles,
  plot titles, and save-directory rules.
- Lab methods normally register on `.m`, and lab plots normally register on
  `.p`. Both may also use a custom accessor.
- See the main [README](../README.md#create-a-lab-package) for creation,
  configuration, installation, and loading instructions.
- See the [extension template](../template/README.md) for naming rules and the
  recommended package layout.
- See [demo 4](../demos/demo4.ipynb) for a minimal HDF5 loading backend.
