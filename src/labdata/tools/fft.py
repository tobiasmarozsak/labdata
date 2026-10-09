import numpy as np


def fft(image):
    image = np.fft.ifftshift(np.asarray(image))
    return np.fft.fftshift(np.fft.fft2(image, norm="ortho"))


def ifft(image):
    image = np.fft.ifftshift(np.asarray(image))
    return np.fft.fftshift(np.fft.ifft2(image, norm="ortho"))


def resize(image, sub=None, sup=None):
    image = np.asarray(image)
    result = image.copy()
    if sub is not None:
        result = ifft(resize(fft(result), sup=sub))
        result *= np.sqrt(result.size / image.size)
    if sup is not None:
        old_shape = result.shape
        new_shape = np.round(np.asarray(old_shape) * sup).astype(int)
        pad = []
        cut = []
        for old, new in zip(old_shape, new_shape):
            index = abs(old // 2 - new // 2)
            if old >= new:
                pad.append((0, 0))
                cut.append(slice(index, index + new))
            else:
                pad.append((index, new - old - index))
                cut.append(slice(None))
        result = np.pad(result[tuple(cut)], tuple(pad))
    return result
