from labdata import config


def ravel(mapping, separator=None):
    separator = config.SEPARATOR if separator is None else separator
    result = {}
    for key, value in mapping.items():
        if isinstance(value, dict) and value:
            keys = (key, *value)
            invalid = next(
                (item for item in keys if isinstance(item, str) and separator in item),
                None,
            )
            if invalid is not None:
                raise ValueError(
                    f"Nested key {invalid!r} contains reserved separator "
                    f"{separator!r}"
                )
            for child, item in ravel(value, separator).items():
                result[f"{key}{separator}{child}"] = item
        else:
            result[key] = value
    return result


def unravel(mapping, separator=None):
    separator = config.SEPARATOR if separator is None else separator
    result = {}
    for path, value in mapping.items():
        current = result
        parts = path.split(separator)
        if separator in path and any(not part for part in parts):
            raise ValueError(
                f"Field path {path!r} contains an empty path component"
            )
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result
