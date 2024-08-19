import re
import operator
from jurialmunkey.modimp import importmodule
from jurialmunkey.parser import split_items


def is_excluded(item, filter_key=None, filter_value=None, filter_operator=None, exclude_key=None, exclude_value=None, exclude_operator=None, is_listitem=False):
    """ Checks if item should be excluded based on filter/exclude values
    Values can optional be a dict which contains module, method, and kwargs
    """
    def mod_regex_days(string, external, internal):
        from tmdbhelper.lib.addon.tmdate import get_todays_date
        return string.replace(external, get_todays_date(int(internal)))

    def mod_regex(string):
        regex_func = [
            (r'\$DAYS\[(.*?)\]', mod_regex_days),
        ]

        for regex, func in regex_func:
            result = re.search(regex, string)
            if not result:
                continue
            external = result.group(0)
            internal = result.group(1)
            return func(string, external, internal)

        return string

    def is_filtered(d, k, v, exclude=False, operator_type=None):
        if isinstance(v, str):
            v = mod_regex(v)
        if isinstance(v, dict):
            func = importmodule(v['module'], v['method']) if 'module' in v else v['method']
            v = func(**v['kwargs'])
        comp = getattr(operator, operator_type or 'contains')
        boolean = False if exclude else True  # Flip values if we want to exclude instead of include

        if k and v and k in d and comp(str(d[k]).lower(), str(v).lower()):
            boolean = exclude

        return boolean

    if not item:
        return

    if is_listitem:
        il, ip = item.infolabels, item.infoproperties
    else:
        il, ip = item.get('infolabels', {}), item.get('infoproperties', {})

    if filter_key and filter_value:
        _exclude = True
        for fv in split_items(filter_value):
            _exclude = True
            if is_listitem and fv == 'is_empty':  # Only apply is_empty filter to end product
                _exclude = False
                if il.get(filter_key) or ip.get(filter_key):
                    _exclude = True
                    continue
            if filter_key in il:
                _exclude = False
                if is_filtered(il, filter_key, fv, operator_type=filter_operator):
                    _exclude = True
                    continue
            if filter_key in ip:
                _exclude = False
                if is_filtered(ip, filter_key, fv, operator_type=filter_operator):
                    _exclude = True
                    continue
            if not _exclude:
                break
        if _exclude:
            return True

    if exclude_key and exclude_value:
        for ev in split_items(exclude_value):
            if is_listitem and ev == 'is_empty':  # Only apply is_empty filter to end product
                if not il.get(exclude_key) and not ip.get(exclude_key):
                    return True
            if exclude_key in il:
                if is_filtered(il, exclude_key, ev, True, operator_type=exclude_operator):
                    return True
            if exclude_key in ip:
                if is_filtered(ip, exclude_key, ev, True, operator_type=exclude_operator):
                    return True
