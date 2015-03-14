__author__ = 'bromix'

__all__ = ['create_path', 'create_uri_path', 'strip_html_from_text', 'print_items', 'find_best_fit', 'to_utf8',
           'to_unicode']

import urllib
import re


def to_utf8(text):
    result = text
    if isinstance(text, unicode):
        result = text.encode('utf-8')
        pass

    return result


def to_unicode(text):
    result = text
    if isinstance(text, str):
        result = text.decode('utf-8')
        pass

    return result


def find_best_fit(data, compare_method=None):
    result = None

    last_fit = -1
    if isinstance(data, dict):
        for key in data.keys():
            item = data[key]
            fit = abs(compare_method(item))
            if last_fit == -1 or fit < last_fit:
                last_fit = fit
                result = item
                pass
            pass
        pass
    elif isinstance(data, list):
        for item in data:
            fit = abs(compare_method(item))
            if last_fit == -1 or fit < last_fit:
                last_fit = fit
                result = item
                pass
            pass
        pass

    return result


def create_path(*args):
    comps = []
    for arg in args:
        if isinstance(arg, list):
            return create_path(*arg)

        comps.append(unicode(arg.strip('/').replace('\\', '/').replace('//', '/')))
        pass

    uri_path = '/'.join(comps)
    if uri_path:
        return u'/%s/' % uri_path

    return '/'


def create_uri_path(*args):
    comps = []
    for arg in args:
        if isinstance(arg, list):
            return create_uri_path(*arg)

        comps.append(arg.strip('/').replace('\\', '/').replace('//', '/').encode('utf-8'))
        pass

    uri_path = '/'.join(comps)
    if uri_path:
        return urllib.quote('/%s/' % uri_path)

    return '/'


def strip_html_from_text(text):
    """
    Removes html tags
    :param text: html text
    :return:
    """
    return re.sub('<[^<]+?>', '', text)


def print_items(items):
    """
    Prints the given test_items. Basically for tests
    :param items: list of instances of base_item
    :return:
    """
    if not items:
        items = []
        pass

    for item in items:
        print item
        pass
    pass