import numpy as np
from scipy import ndimage
from scipy.ndimage import gaussian_filter
from scipy.signal import fftconvolve


def inversion_centre(image, sigma=5):
    image = np.asarray(image)
    img = np.nan_to_num(image, nan=0, posinf=0, neginf=0)
    img = gaussian_filter(img, sigma=sigma)
    img = fftconvolve(img, img, mode="same")
    img = gaussian_filter(img, sigma=sigma)
    peak = np.unravel_index(np.argmax(img), img.shape)
    return (peak + np.asarray(image.shape) // 2) // 2


def clip_roi(image, roi):
    image = np.asarray(image)
    return (
        int(np.clip(roi[0], 0, image.shape[0])),
        int(np.clip(roi[1], 0, image.shape[0])),
        int(np.clip(roi[2], 0, image.shape[1])),
        int(np.clip(roi[3], 0, image.shape[1])),
    )


def centre_roi(image, size, centre=None):
    image = np.asarray(image)
    if centre is None:
        centre = inversion_centre(image)
    size = np.broadcast_to(size, image.ndim).astype(int)
    centre = np.asarray(centre, dtype=int)
    corner = centre - size // 2
    return clip_roi(
        image,
        (
            corner[0],
            corner[0] + size[0],
            corner[1],
            corner[1] + size[1],
        ),
    )


def crop(image, roi):
    image = np.asarray(image)
    start_row, stop_row, start_column, stop_column = clip_roi(image, roi)
    result = image[start_row:stop_row, start_column:stop_column].view()
    result.flags.writeable = False
    return result


def normalize(image, edge=5):
    image = np.asarray(image)
    border = np.ones(image.shape, dtype=bool)
    border[edge:-edge, edge:-edge] = False
    return image - np.nanmean(image[border])


def rotate(image, angle, centre=None, **kwargs):
    image = np.asarray(image)
    if centre is None:
        centre = inversion_centre(image)
    centre = np.asarray(centre)
    shape = image.shape
    pad0 = [shape[0] - centre[0], centre[0]]
    pad1 = [shape[1] - centre[1], centre[1]]
    image = np.pad(image, [pad0, pad1], "constant")
    image = ndimage.rotate(image, angle, reshape=False, **kwargs)
    return image[pad0[0]:pad0[0] + shape[0], pad1[0]:pad1[0] + shape[1]]
