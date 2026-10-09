import numpy as np

from labdata.tools.fit import lsfit
from labdata.methods.core import cache


@cache()
def parabola(x, y, p0=None, **kwargs):
    x = np.asarray(x)
    y = np.asarray(y)
    if p0 is None:
        p0 = guess(x, y)
    return lsfit(x, y, fun=model, p0=p0, **kwargs)


def model(x, quad_coeff, lin_coeff, intercept):
    return quad_coeff * x**2 + lin_coeff * x + intercept


def guess(x, y):
    quad_coeff, lin_coeff, intercept = np.polyfit(x, y, 2)
    return {
        "quad_coeff": quad_coeff,
        "lin_coeff": lin_coeff,
        "intercept": intercept,
    }
