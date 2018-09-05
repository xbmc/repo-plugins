def find(findFn, l):
    """
      Will return the first item matching the findFn
      findFn: A function taking one param: value. MUST return a boolean
      l: The list to search
    """
    for item in l:
        if findFn(item):
            return item
    return None


def find_dict(findFn, d):
    """
      Will return the first value matching the findFn
      findFn: A function taking two params: value, key. MUST return a boolean
      d: The dict to search
    """
    for k, v in d.iteritems():
        if findFn(v, k):
            return v
    return None


def map_dict(mapFn, d):
    """
      mapFn: A function taking two params: value, key
      d: The dict to map
    """
    return {k: mapFn(v, k) for k, v in d.iteritems()}


def filter_dict(filterFn, d):
    """
      filterFn: A function taking two params: value, key. MUST return a boolean
      d: The dict to filter
    """
    return {k: v for k, v in d.iteritems() if filterFn(v, k)}


def reject_dict(filterFn, d):
    """
      filterFn: A function taking two params: value, key. MUST return a boolean
      d: The dict to filter
    """
    def invert(*args, **kwargs):
        return not filterFn(*args, **kwargs)
    return filter_dict(invert, d)


def get_property(d, path, default=None):
    def walk(sub_d, segment):
        if sub_d is None:
            return None
        return sub_d.get(segment)
    segments = path.split('.')
    return reduce(walk, segments, d) or default


def merge_dicts(*args):
    result = {}
    for d in args:
        result.update(d)
    return result


def flatten(l):
    return [item for sublist in l for item in sublist]
