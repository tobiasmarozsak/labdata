import matplotlib as mpl
import matplotlib.pyplot as plt

from labdata.plots.core import figure, register


@register
@figure("wikilight", subplots=True)
def pairplot(data, vars, cmap=None, norm=None, **kwargs):
    import seaborn as sns

    fields = list(vars)
    hue = kwargs.get("hue")
    if hue is not None and hue not in fields:
        fields.append(hue)
    values = data[fields].dropna(subset=vars)

    if hue is None:
        color = mpl.rcParams["axes.prop_cycle"].by_key()["color"][0]
        kwargs["plot_kws"] = {"color": color, **kwargs.get("plot_kws", {})}
        kwargs["diag_kws"] = {
            "color": color,
            "alpha": 1,
            **kwargs.get("diag_kws", {}),
        }

    with plt.ion():
        grid = sns.pairplot(values, vars=vars, **kwargs)
    canvas = grid.figure
    for ax in grid.axes.flat:
        if ax is not None:
            for spine in ax.spines.values():
                spine.set_visible(True)

    if cmap is not None:
        cmap = mpl.colormaps.get_cmap(cmap)
        norm = mpl.colors.Normalize(-1, 1) if norm is None else norm
        corr = values[vars].corr()
        for row, y in enumerate(grid.y_vars):
            for column, x in enumerate(grid.x_vars):
                if row != column:
                    grid.axes[row, column].set_facecolor(cmap(norm(corr.loc[y, x])))

    return canvas, grid
