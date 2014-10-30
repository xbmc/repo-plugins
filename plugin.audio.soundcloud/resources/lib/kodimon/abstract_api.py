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


def json_to_item(json_data):
    """
    Creates a instance of the given json dump or dict.
    :param json_data:
    :return:
    """

    def _from_json(_json_data):
        from . import VideoItem, DirectoryItem

        mapping = {'VideoItem': lambda: VideoItem(u'', u''),
                   'DirectoryItem': lambda: DirectoryItem(u'', u'')}

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
        from . import VideoItem, DirectoryItem

        if isinstance(obj, dict):
            return obj.__dict__

        mapping = {VideoItem: 'VideoItem',
                   DirectoryItem: 'DirectoryItem'}

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
            _seconds = _time2[2].split('.')[0]
            _result['second'] = int(_seconds)
            pass

        if len(_split_time) > 1:
            _time3 = _split_time[1].split(':')
            _result['offset_hour'] = int(_time3[0])
            if _time.find('-') != -1:
                _result['offset_hour'] *= -1
            pass

        if _time.endswith('Z'):
            _result['offset_hour'] = 0
            pass

        return _result

    def _parse_period(_iso_8601_string):
        _result = {}

        re_match = re.match('P((?P<years>\d+)Y)?((?P<months>\d+)M)?((?P<days>\d+)D)?(T((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+)S)?)?', _iso_8601_string)
        if re_match:
            _result['years'] = re_match.group('years')
            _result['months'] = re_match.group('months')
            _result['days'] = re_match.group('days')
            _result['hours'] = re_match.group('hours')
            _result['minutes'] = re_match.group('minutes')
            _result['seconds'] = re_match.group('seconds')

            for key in _result:
                value = _result[key]
                if value is None:
                    _result[key] = 0
                elif isinstance(value, basestring):
                    _result[key] = int(value)
                    pass
                pass
            pass

        return _result

    result = {}

    _data = re.split('T| ', iso_8601_string)

    # period
    if _data[0] == 'P':
        return _parse_period(iso_8601_string)

    result.update(_parse_date(_data[0]))
    if len(_data) > 1:
        result.update(_parse_time(_data[1]))
        pass

    return result


def create_uri_path(*args):
    def _process_list(comps):
        _path = []
        for comp in comps:
            if comp:
                _path.append(comp.strip('/').encode('utf-8'))
                pass
            pass
        return _path

    def _process_string(str):
        str = str.replace('\\', '/')
        return _process_list(str.split('/'))

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
    Prints the given items. Basically for tests
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