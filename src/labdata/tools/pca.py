import numpy as np
from scipy.ndimage import gaussian_filter


def pca(images, num=None, sigma=2):
    images = np.nan_to_num(np.asarray(images))
    if sigma > 0:
        images = np.asarray([gaussian_filter(image, sigma=sigma) for image in images])
    if num is None:
        num = images.shape[0]

    matrix = images.reshape(images.shape[0], -1)
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    return {
        "modes": vh.reshape((-1, *images.shape[1:]))[:num],
        "values": s[:num],
        "coeffs": u.T[:num],
    }
