import numpy as np

from labdata import tools
from labdata.methods.core import method, register


@register
@method()
def pca(data, num=None, sigma=2):
    records = [data] if isinstance(data, dict) else data
    images = [
        np.where(record["MASK"], record["IMAGE"], np.nan)
        if "MASK" in record
        else record["IMAGE"]
        for record in records
    ]
    result = tools.pca(images, num=num, sigma=sigma)
    for index, record in enumerate(records):
        record.setdefault("var", {}).update({
            f"coeff_{mode}": result["coeffs"][mode, index]
            for mode in range(len(result["coeffs"]))
        })
        record["PCA"] = {
            "modes": result["modes"],
            "values": result["values"],
        }
    return records[0] if isinstance(data, dict) else records
