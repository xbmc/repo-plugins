"""Utility methods"""


def to_bool(value: str) -> bool:
    """Returns a boolean from a string
    :param value: The boolean as a string
    :raise ValueError if value is not "true" of "false"
    """
    if value is None:
        raise ValueError("Input value can't be none")

    value = value.lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("Input value must be 'true' or 'false'")
