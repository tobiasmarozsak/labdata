import numpy as np

from labdata import tools
from labdata.methods.core import method, register


@register
@method(vectorise=True)
def pixelsum(data, roi=None, refroi=None, image="IMAGE"):
    values = data[image]
    if "MASK" in data:
        values = np.where(data["MASK"], values, np.nan)
    if refroi is not None:
        values = values - np.nanmean(tools.crop(values, refroi))

    source = data.get("METADATA", {}).get(
        "ROI",
        (0, values.shape[0], 0, values.shape[1]),
    )
    if roi is None:
        roi = (0, values.shape[0], 0, values.shape[1])
    roi = tools.clip_roi(values, roi)
    values = np.nan_to_num(tools.crop(values, roi), nan=0, posinf=0, neginf=0)

    rows, columns = np.indices(values.shape)
    total = np.sum(values)
    y_centre = np.sum(rows * values) / total
    x_centre = np.sum(columns * values) / total
    y_sigma = np.sqrt(np.abs(np.sum((rows - y_centre) ** 2 * values) / total))
    x_sigma = np.sqrt(np.abs(np.sum((columns - x_centre) ** 2 * values) / total))

    data.setdefault("var", {}).update({
        "x_centre[pixel]": x_centre + source[2] + roi[2],
        "y_centre[pixel]": y_centre + source[0] + roi[0],
        "x_sigma[pixel]": x_sigma,
        "y_sigma[pixel]": y_sigma,
        "sigma[pixel]": np.sqrt((x_sigma**2 + y_sigma**2) / 2),
        "pixelsum": total,
    })
    return data
