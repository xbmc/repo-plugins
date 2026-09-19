"""Utilities to write log files with API and Kodi display traces."""

from os.path import join as OSPJoin
from datetime import datetime
import json
import xbmcgui
import xbmcvfs

from resources.lib.native_plugin import Plugin
from . import settings


def log_json(reply, log_suffix, redact_body=False):
    """save request and response in reply into a file
    with file name containing log_suffix in addon user data
    if loglevel settings is set to API.
    :param reply Python requests library object with every information to log
    :param log_suffix string to be used in log file name along current date and time
    """
    plugin = Plugin()
    msettings = settings.Settings(plugin)
    if reply is None or not msettings.should_log('API'):
        return

    base_path = plugin.storage_path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    log_path = OSPJoin(base_path, f"{timestamp}_{log_suffix}-api.json")
    reqhdrs = format_headers(reply.request.headers)
    reshdrs = format_headers(reply.headers)
    with xbmcvfs.File(log_path, 'w') as log_file:
        log_file.write("---------------- request ----------------\n")
        log_file.write(f"{reply.request.method} {reply.request.url}\n")
        log_file.write(f"{reqhdrs}\n")
        log_file.write(f"payload : {'<redacted>' if redact_body else reply.request.body}\n")
        log_file.write("---------------- response ----------------\n")
        log_file.write(f"{reply.status_code} {reply.reason} {reply.url}\n")
        log_file.write(f"{reshdrs}\n")
        log_file.write(f"payload : {'<redacted>' if redact_body else reply.text}")


def log_xbmc(payload, log_suffix):
    """Serialize xbmc objects and listitems as JSON into addon storage."""
    plugin = Plugin()
    msettings = settings.Settings(plugin)
    if payload is None or not msettings.should_log('DISPLAY'):
        return

    base_path = plugin.storage_path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    log_path = OSPJoin(base_path, f"{timestamp}_{log_suffix}-xbmc.json")
    with xbmcvfs.File(log_path, 'w') as log_file:
        payload_json = json.dumps(
            to_jsonable(payload), indent=2, sort_keys=True, ensure_ascii=False)
        log_file.write(payload_json)


def to_jsonable(payload):
    """Recursively convert native Python values and Kodi objects to JSON-safe data."""
    if payload is None or isinstance(payload, (str, int, float, bool)):
        return payload
    if isinstance(payload, (list, tuple)):
        return [to_jsonable(item) for item in payload]
    if isinstance(payload, dict):
        return {str(key): to_jsonable(value) for key, value in payload.items()}
    if isinstance(payload, xbmcgui.ListItem):
        return get_dict_from_list_item(payload)
    if isinstance(payload, bytes):
        return payload.decode('utf-8', 'replace')

    data = {}
    if hasattr(payload, '__dict__'):
        for attr_name, attr_value in vars(payload).items():
            if attr_name.startswith('_') or callable(attr_value):
                continue
            data[attr_name] = to_jsonable(attr_value)

    if not data:
        data = {'__repr__': repr(payload)}

    return {
        '__type__': f"{payload.__class__.__module__}.{payload.__class__.__name__}",
        **data,
    }


def format_headers(headers) -> str:
    """Map headers into a readable string to be logged."""
    return '\n'.join(f'{k}: {v}' for k, v in _redact_value(dict(headers)).items())


def _is_sensitive_field(key):
    """Determine if a field name is considered sensitive and should be redacted."""
    normalized = str(key).lower().replace('-', '').replace('_', '').replace(' ', '')
    return (
        # no upper case, no dash, no underscore, no space in the list of sensitive fields
        # because the key is normalized before checking
        normalized in ['password', 'pwd', 'secret', 'email', 'mail', 'username', 'user', 'login',
                       'uid', 'userid', 'usercode', 'devicecode',
                       'authorization', 'proxyauthorization', 'cookie', 'setcookie', 'xapikey',
                       ]
        or normalized.endswith('token')
    )


def _redact_value(value):
    """
    Recursively redact sensitive fields in a value.
    Check is key is sensitive in case of dict, otherwise redact the value itself.
    """
    if isinstance(value, dict):
        return {
            key: '<redacted>' if _is_sensitive_field(key) else item
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    if isinstance(value, str):
        return '<redacted>'
    return value


def get_dict_from_info_tag_video(li):
    """Extract common video InfoTag fields from a ListItem's VideoInfoTag into a dict.

    This probes the tag for known getters and only calls them when present,
    avoiding broad exception handling.
    """
    if not hasattr(li, 'getVideoInfoTag'):
        return None

    tag = li.getVideoInfoTag()
    if not tag:
        return None

    info = {}
    info['title'] = tag.getTitle()
    info['plot'] = tag.getPlot()
    info['plotoutline'] = tag.getPlotOutline()
    # No mpaa exposed, but Nexus and earlier does
    if hasattr(tag, 'getMpaa'):
        info['mpaa'] = tag.getMpaa()
    info['duration'] = tag.getDuration()
    info['firstairedasw3c'] = tag.getFirstAiredAsW3C()
    genres = tag.getGenres()
    info['genres'] = list(genres) if genres is not None else None
    directors = tag.getDirectors()
    info['directors'] = list(directors) if directors is not None else None
    actors = tag.getActors()
    if isinstance(actors, list):
        info['actors'] = []
        for actor in actors:
            info['actors'].append({'name': actor.getName(), 'role': actor.getRole()})
    writers = tag.getWriters()
    info['writers'] = list(writers) if writers is not None else None
    # No countries exposed, but Nexus and earlier does
    if hasattr(tag, 'getCountries'):
        countries = tag.getCountries()
        info['countries'] = list(countries) if countries is not None else None
    info['year'] = tag.getYear()

    return info


def get_dict_from_list_item(li):
    """
    Serialize an xbmcgui.ListItem into a plain dict so it can be
    JSON-serialized / persisted. Be defensive: not all ListItem
    implementations expose the same getter methods, so wrap calls.
    """
    result = {}
    result['label'] = li.getLabel()
    result['path'] = li.getPath()
    result['art'] = {}
    for art_key in ['thumb', 'fanart']:
        result['art'][art_key] = li.getArt(art_key)
    props = {}
    if hasattr(li, 'getProperties'):
        props = li.getProperties()
    else:
        # fall back to probing a set of commonly used property keys
        if hasattr(li, 'getProperty'):
            for key in ('is_playable', 'StartOffset', 'StartPercent'):
                val = li.getProperty(key)
                if val is not None and val != '':
                    props[key] = val
    result['properties'] = props

    # info labels (metadata)
    if hasattr(li, 'getInfoLabels') and li.getInfoLabels():
        result['info'] = li.getInfoLabels()

    # video InfoTag (detailed metadata) when available
    result['video_info_tag'] = get_dict_from_info_tag_video(li)

    return result
