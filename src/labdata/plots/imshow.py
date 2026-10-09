import matplotlib as mpl
import numpy as np

from labdata.plots.core import register, subplot


@register
@subplot
def imshow(data, z="IMAGE", *, ax, **kwargs):
    kwargs.setdefault("cmap", mpl.colormaps["turbo"])
    kwargs.setdefault("origin", "lower")
    image = np.nan_to_num(np.asarray(data[z]))
    if "norm" not in kwargs:
        kwargs.setdefault("vmin", np.nanmedian(image))
        kwargs.setdefault("vmax", np.nanmax(image))
    artist = ax.imshow(image, **kwargs)
    ax.set_aspect(1)
    ax.autoscale(enable=False)
    ax.set_xticks([])
    ax.set_yticks([])
    return artist


@register
@subplot
def crosshair(data, y=None, x=None, angle=0, *, ax, **kwargs):
    kwargs.setdefault("color", "yellow")
    kwargs.setdefault("marker", "none")
    kwargs.setdefault("ls", "-")
    artists = []

    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    centre_x = sum(xlim) / 2 if x is None else x
    centre_y = sum(ylim) / 2 if y is None else y
    transform = mpl.transforms.Affine2D().rotate_deg_around(
        centre_x, centre_y, angle
    ) + ax.transData

    if y is not None:
        width = abs(xlim[1] - xlim[0])
        artists += ax.plot(
            [centre_x - width, centre_x + width], [y, y],
            transform=transform, **kwargs,
        )
    if x is not None:
        height = abs(ylim[1] - ylim[0])
        artists += ax.plot(
            [x, x], [centre_y - height, centre_y + height],
            transform=transform, **kwargs,
        )

    return artists
