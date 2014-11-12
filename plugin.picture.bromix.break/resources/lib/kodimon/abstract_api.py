import json
import urllib
import re


def run(provider):
    """
    Must be implemented.
    :param provider:
    """
    raise NotImplementedError()


def sort_items_by_name(content_items=None, reverse=False):
    """
    Sort the list of test_items based on their name.
    :param content_items:
    :param reverse:
    :return:
    """
    if not content_items:
        content_items = []

    def _sort(item):
        return item.get_name().upper()

    return sorted(content_items, key=_sort, reverse=reverse)


def create_uri_path(*args):
    def _process_list(comps):
        _path = []
        for comp in comps:
            if comp:
                _path.append(comp.strip('/').encode('utf-8'))
                pass
            pass
        return _path

    def _process_string(_str):
        _str = _str.replace('\\', '/')
        return _process_list(_str.split('/'))

    path = []
    for arg in args:
        if isinstance(arg, basestring):
            path.extend(_process_string(arg))
        elif isinstance(arg, list):
            path.extend(_process_list(arg))
        pass

    path = '/'.join(path)
    if path:
        path = path.replace('//', '/')
        return urllib.quote('/%s/' % path)

    return ''


def create_plugin_uri(plugin, path=None, params=None):
    if not path:
        path = ''
        pass

    if not params:
        params = {}
        pass

    _path = create_uri_path(path)

    uri = ""
    if _path:
        uri = "%s://%s%s" % ('plugin', plugin.get_id().encode('utf-8'), _path)
    else:
        uri = "%s://%s/" % ('plugin', plugin.get_id().encode('utf-8'))

    if len(params) > 0:
        # make a copy of the map
        _params = {}
        _params.update(params)

        # encode in utf-8
        for param in _params:
            _params[param]=params[param].encode('utf-8')
            pass
        uri = uri + '?' + urllib.urlencode(_params)
        pass

    return uri


def strip_html_from_text(text):
    """
    Returns a html free text
    :param text: text with html tags
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