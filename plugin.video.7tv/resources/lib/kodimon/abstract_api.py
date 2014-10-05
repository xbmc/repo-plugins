import json
import urllib
import re

"""
Abstract declaration of global methods. The methods must be implemented and will
be overridden by the import of the implementation.

This prevents us from forgetting to write methods in the implementation.
"""


def debug_here():
    """
    For debugging at a particular position in your plugin call this method.
    :return:
    """
    import pydevd

    pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    pass


def run(provider):
    """
    Needs to be implemented by a mock for testing or the real deal.
    This will execute the provider and pipe the content to kodi.
    :param provider:
    :return:
    """
    raise NotImplementedError()


def log(text, log_level=2):
    """
    Needs to be implemented by a mock for testing or the real deal.
    Logging.
    :param text:
    :param log_level:
    :return:
    """
    raise NotImplementedError()


def create_content_path(*args):
    """
    This will return a clean path by the given string or list of strings ['path1', 'path2']
    :param path_list:
    :return:
    """

    quoted_list = []
    for arg in args:
        if isinstance(arg, basestring):
            u_str = unicode(arg)
            quoted_list.append(urllib.quote(u_str.strip('/')))
        elif isinstance(arg, list):
            for item in arg:
                u_str = unicode(item)
                quoted_list.append(urllib.quote(u_str.strip('/')))
                pass
            pass
        pass

    result = "/".join(quoted_list)
    result = result.replace('//', '/')
    result = "/" + result + "/"
    return result


def json_to_item(json_data):
    """
    Creates a instance of the given json dump or dict.
    :param json_data:
    :return:
    """

    def _from_json(_json_data):
        from . import VideoItem, DirectoryItem, SearchItem

        mapping = {'VideoItem': lambda: VideoItem(u'', u''),
                   'DirectoryItem': lambda: DirectoryItem(u'', u''),
                   'SearchItem': lambda: SearchItem(u'')}

        item = None
        item_type = _json_data.get('type', None)
        for key in mapping:
            if item_type == key:
                item = mapping[key]()
                break
            pass

        if item is None:
            return _json_data

        data = _json_data.get('data', {})
        for key in data:
            if hasattr(item, key):
                setattr(item, key, data[key])
                pass
            pass

        return item

    if isinstance(json_data, basestring):
        json_data = json.loads(json_data)
    return _from_json(json_data)


def item_to_json(base_item):
    """
    Convert the given @base_item to json
    :param base_item:
    :return: json string
    """

    def _to_json(obj):
        from . import VideoItem, DirectoryItem, SearchItem

        if isinstance(obj, dict):
            return obj.__dict__

        mapping = {VideoItem: 'VideoItem',
                   DirectoryItem: 'DirectoryItem',
                   SearchItem: 'SearchItem'}

        for key in mapping:
            if isinstance(obj, key):
                return {'type': mapping[key], 'data': obj.__dict__}
            pass

        return obj.__dict__

    return _to_json(base_item)


def sort_items_by_name(content_items=None, reverse=False):
    """
    Sort the list of items based on their name.
    :param content_items:
    :param reverse:
    :return:
    """
    if not content_items:
        content_items = []

    def _sort(item):
        return item.get_name().upper()

    return sorted(content_items, key=_sort, reverse=reverse)


def sort_items_by_info_label(content_items, info_type, reverse=False):
    """
    Sort the list of item based on the given info label.
    :param content_items:
    :param info_type:
    :param reverse:
    :return:
    """

    def _sort(item):
        return item.get_info(info_type)

    sorted_list = sorted(content_items, key=_sort, reverse=reverse)
    return sorted_list


def parse_iso_8601(iso_8601_string):
    def _parse_date(_date):
        _result = {}
        _split_date = _date.split('-')
        if len(_split_date) > 0:
            _result['year'] = int(_split_date[0])
            pass
        if len(_split_date) > 1:
            _result['month'] = int(_split_date[1])
            pass
        if len(_split_date) >= 2:
            _result['day'] = int(_split_date[2])
            pass

        return _result

    def _parse_time(_time):
        _result = {}
        _split_time = re.split('[-+]', _time)

        _time2 = _split_time[0].split(':')
        if len(_time2) > 0:
            _result['hour'] = int(_time2[0])
            pass
        if len(_time2) > 1:
            _result['minute'] = int(_time2[1])
            pass
        if len(_time2) >= 2:
            _result['second'] = int(_time2[2])
            pass

        if len(_split_time) > 1:
            _time3 = _split_time[1].split(':')
            _result['offset_hour'] = int(_time3[0])
            if _time.find('-') != -1:
                _result['offset_hour'] *= -1
            pass
        return _result

    result = {}

    _data = iso_8601_string.split('T')
    result.update(_parse_date(_data[0]))
    if len(_data) > 1:
        result.update(_parse_time(_data[1]))
        pass

    return result


def create_plugin_url(plugin, path='', params=None):
    """
    Creates a url for the given plugin
    :param plugin: current plugin
    :param path: current path
    :param params: optional params
    :return:
    """
    if not params:
        params = {}

    url = ""
    if path is not None and len(path) > 0:
        url = "%s://%s/%s/" % ('plugin', plugin.get_id(), path.strip('/'))
    else:
        url = "%s://%s/" % ('plugin', plugin.get_id())

    if params is not None and len(params) > 0:
        url = url + '?' + urllib.urlencode(params)
        pass

    return url


def create_url_from_item(plugin, base_item):
    """
    Creates a url based on the given plugin and BaseItem
    :param plugin:
    :param base_item:
    :return:
    """
    return create_plugin_url(plugin, base_item.get_path(), base_item.get_params())