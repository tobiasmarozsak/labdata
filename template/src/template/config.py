from pathlib import Path

from . import load


DATA_FOLDER = Path()                     # Path-like local data root
DATA_FOLDER_ALIASES = ()                 # Iterable of historical path-like roots
DATA_FILE_PATTERN = r"(?i).*\.h5$"       # Full-match filename regex string
LOAD_BACKEND = load.backend              # Callable(open_file) -> reader module
CACHE_FOLDER = None                      # Path-like local file cache

SEPARATOR = None                         # String joining nested field names
DEFAULT_IMAGE = None                     # Preferred image name (e.g. OD)
DEFAULT_COLORBAR = None                  # (lower, upper) numeric tuple

PLOT_STYLE = None                        # Path-like Matplotlib style
TABLE_STYLE = None                       # Path-like Matplotlib table style
WIDGET_CSS = None                        # Path-like notebook CSS resource
VIEW_QSS = None                          # Path-like Qt QSS resource
PLOT_TITLE = None                        # Callable(DataFrame) -> string
SAVE_DIRECTORY = None                    # Callable(sequence[Path]) -> path-like
