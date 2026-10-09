import numpy as np

from labdata import tools
from labdata.methods.core import method, register


@register
@method(vectorise=True)
def fft(data, window=None, image="IMAGE"):
    values = data[image]
    if "MASK" in data:
        values = np.where(data["MASK"], values, np.nan)
    values = np.nan_to_num(values, nan=0, posinf=0, neginf=0)
    if window is not None:
        values = values * window(values.shape[0])[:, None]
        values = values * window(values.shape[1])[None, :]

    result = tools.fft(values)
    data["FFT"] = {
        "IMAGE": result,
        "x[1/pixel]": np.fft.fftshift(np.fft.fftfreq(result.shape[1])),
        "y[1/pixel]": np.fft.fftshift(np.fft.fftfreq(result.shape[0])),
    }
    return data
