"""Utility methods for lists and dictionaries"""

def find(find_fctn, lst):
    """
      Return the first item matching the findfctn
      :param fn find_fctn: A function taking one param: value. MUST return a boolean
      :param list lst: The list to search
    """
    for item in lst:
        if find_fctn(item):
            return item
    return None


def find_dict(find_fctn, dictionary):
    """
      Return the first value matching the findfctn
      :param fn find_fctn: A function taking two params: value, key. MUST return a boolean
      :param dict dictionary: The dict to search
    """
    for key, value in dictionary.items():
        if find_fctn(value, key):
            return value
    return None


def map_dict(map_fctn, dictionary):
    """
      :param fn map_fctn: A function taking two params: value, key
      :param dict dictionary: The dict to map
    """
    return {k: map_fctn(v, k) for k, v in dictionary.items()}


def filter_dict(filter_fctn, dictionary):
    """
      :param fn filter_fctn: A function taking two params: value, key. MUST return a boolean
      :param dict dictionary: The dict to filter
    """
    return {key: value for key, value in dictionary.items() if filter_fctn(value, key)}

def merge_dicts(*args):
    """
      Merge dictionaries in a single one. Precedence on lastest dictionaries in args
    """
    result = {}
    for dictionary in args:
        result.update(dictionary)
    return result

def flat_map(fctn, lst):
    """Return the results of applying fctn on sub elements of lst."""
    return [item for list_item in lst for item in fctn(list_item)]
