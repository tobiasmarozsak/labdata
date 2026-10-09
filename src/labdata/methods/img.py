import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

from labdata import tools
from labdata.methods.core import method, register
from labdata.tools.mapping import unravel


@register
@method(vectorise=True)
def imagecrop(data, roi=None, *, size=None, centre=None):
    image = data["IMAGE"]
    if roi is None:
        roi = tools.centre_roi(image, size, centre)
    else:
        roi = tools.clip_roi(image, roi)

    metadata = data.setdefault("METADATA", {})
    source = metadata.get("ROI", (0, image.shape[0], 0, image.shape[1]))
    data["IMAGE"] = tools.crop(image, roi)
    if "MASK" in data:
        data["MASK"] = tools.crop(data["MASK"], roi)
    metadata["ROI"] = (int(source[0] + roi[0]), int(source[0] + roi[1]), int(source[2] + roi[2]), int(source[2] + roi[3]))
    return data


@register
@method(vectorise=True)
def imagenorm(data, *, refroi=None, excroi=None, border=None):
    image = data["IMAGE"]
    if border is not None:
        excroi = (border, image.shape[0] - border, border, image.shape[1] - border)
    if refroi is not None:
        offset = np.nanmean(tools.crop(image, refroi))
    elif excroi is not None:
        reference = np.array(image, copy=True)
        roi = tools.clip_roi(image, excroi)
        reference[roi[0]:roi[1], roi[2]:roi[3]] = np.nan
        offset = np.nanmean(reference)
    else:
        offset = np.nanmedian(image)
    data["IMAGE"] = image - offset
    return data


@register
@method(vectorise=True)
def imagemask(data, vmin=None, vmax=None, sigma=0):
    image = np.nan_to_num(data["IMAGE"])
    if sigma > 0:
        image = gaussian_filter(image, sigma=sigma)
    mask = data.get("MASK", np.ones(image.shape, dtype=bool)).astype(bool)
    if vmin is not None:
        mask = mask & (image > vmin)
    if vmax is not None:
        mask = mask & (image < vmax)
    data["MASK"] = mask
    return data


@register
@method(vectorise=True)
def imagerotate(data, angle, centre=None, **kwargs):
    image = data["IMAGE"]
    if centre is None:
        centre = tools.inversion_centre(image)
    centre = np.asarray(centre)
    data["IMAGE"] = tools.rotate(image, angle, centre, **kwargs)
    if "MASK" in data:
        data["MASK"] = tools.rotate(
            data["MASK"].astype(float), angle, centre, order=0
        ).astype(bool)
    return data


@register
@method()
def imagemean(data, key=None):
    if isinstance(data, dict):
        return data
    if not data:
        return []
    frame = pd.DataFrame(data)
    if key is None:
        frame = frame.groupby([0] * len(frame)).agg(list)
    else:
        frame = frame.groupby(key).agg(list)
    for column in frame:
        if column == "IMAGE":
            frame[column] = frame[column].map(lambda items: np.mean(np.nan_to_num(items), axis=0))
        elif column == "MASK":
            frame[column] = frame[column].map(lambda items: np.mean(np.nan_to_num(items), axis=0).astype(bool))
        elif frame[column].apply(lambda items: len(np.unique([str(item) for item in items])) == 1).all():
            frame[column] = frame[column].map(lambda items: items[0])
    frame = frame.reset_index(drop=key is None)
    return [unravel(record) for record in frame.to_dict("records")]
