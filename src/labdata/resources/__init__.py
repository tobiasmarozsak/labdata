from importlib.resources import files


PLOT_STYLE = files(__package__).joinpath("wikilight.mplstyle")
TABLE_STYLE = files(__package__).joinpath("table.mplstyle")
WIDGET_CSS = files(__package__).joinpath("widgets.css")
VIEW_QSS = files(__package__).joinpath("view.qss")
