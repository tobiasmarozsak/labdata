import numpy as np
from scipy.special import factorial, gamma, spence, zeta


def polylog(order, x):
    """Real Li_order(x) for orders 2 and 2.5 on 0 <= x <= 1."""
    x = np.asarray(x, dtype=float)
    result = np.empty_like(x)
    small = x < np.exp(-1)
    z = x[small]
    power = z.copy()
    value = np.zeros_like(z)
    for k in range(1, 33):
        value += power / k**order
        power *= z
    result[small] = value

    z = x[~small]
    if order == 2:
        result[~small] = spence(1 - z)
    else:
        # Expansion about x=1: https://dlmf.nist.gov/25.12.E12
        t = -np.log(z)
        n = np.arange(20)
        coefficients = zeta(order - n) / factorial(n)
        result[~small] = (gamma(1 - order) * t**(order - 1)
                          + np.polynomial.polynomial.polyval(-t, coefficients))
    return result
