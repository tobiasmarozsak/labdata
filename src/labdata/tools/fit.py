from functools import wraps

import lmfit
import numpy as np
from uncertainties import nominal_value, ufloat, unumpy


def lsfit(x, y, fun, p0, **kwargs):
    x = np.asarray(x).T
    y = np.asarray(y)

    sigma = unumpy.std_devs(y)
    y = unumpy.nominal_values(y)
    weights = kwargs.pop("weights", None)
    if weights is None:
        # Ordinary numbers have zero uncertainty and retain unit weight.
        weights = np.ones_like(y)
        np.divide(1, sigma, out=weights, where=sigma != 0)
    else:
        weights = np.broadcast_to(np.asarray(weights), y.shape)

    mask = np.isfinite(y) & np.isfinite(weights)
    mask &= np.all(np.isfinite(x), axis=tuple(range(1, x.ndim)))
    x, y, weights = x[mask], y[mask], weights[mask]

    if isinstance(p0, dict) and not isinstance(p0, lmfit.Parameters):
        params = {}
        for key, value in p0.items():
            options = value.copy() if isinstance(value, dict) else {"value": value}
            if "value" in options:
                options["value"] = nominal_value(options["value"])
            params[key] = options
        p0 = lmfit.create_params(**params)

    @wraps(fun)
    def model(x, **params):
        return fun(x=x.T, **params)

    fit = lmfit.Model(model, independent_vars=["x"]).fit(
        y, x=x, params=p0, weights=weights, **kwargs
    )
    uvars = getattr(fit, "uvars", None)
    if uvars is None:
        uvars = {key: ufloat(param.value, np.nan) for key, param in fit.params.items()}

    values = {key: param.value for key, param in fit.params.items()}
    return {
        "model": fit,
        "success": fit.success,
        "message": fit.message,
        "nfev": fit.nfev,
        "rsqr": fit.rsquared,
        "chisqr": fit.chisqr,
        "fun": fun,
        "x": x,
        "y": y,
        "weights": weights,
        "best_fit": fit.best_fit,
        "residual": y - fit.best_fit,
        "p": fit.var_names,
        "p0": fit.init_values,
        "popt": values,
        "perr": {key: param.stderr for key, param in fit.params.items()},
        "pcov": fit.covar,
        "var": values.copy(),
        "uvar": uvars.copy(),
    }
