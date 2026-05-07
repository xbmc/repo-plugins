#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import time
import datetime
import os
import operator
import sys
import hashlib

########################

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = ADDON.getAddonInfo('path')

INFO = xbmc.LOGINFO
WARNING = xbmc.LOGWARNING
DEBUG = xbmc.LOGDEBUG
ERROR = xbmc.LOGERROR

DIALOG = xbmcgui.Dialog()

COUNTRY_CODE = ADDON.getSettingString('country_code')
DEFAULT_LANGUAGE = ADDON.getSettingString('language_code')
FALLBACK_LANGUAGE = 'en'

CACHE_ENABLED = ADDON.getSettingBool('cache_enabled')
CACHE_PREFIX = ADDON_ID + '_' + ADDON_VERSION + '_' + DEFAULT_LANGUAGE + COUNTRY_CODE + '_'
CACHE_PATH = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/%s/cache" % ADDON_ID))

TIMEZONE = 'local'

########################

''' Kodi version detection for choosing between modern InfoTagVideo
    (Kodi 20+) and legacy ListItem.setInfo() API.
'''
def _get_kodi_major_version():
    try:
        version_str = xbmc.getInfoLabel('System.BuildVersion')
        return int(version_str.split('.')[0])
    except (ValueError, AttributeError, IndexError):
        return 0

KODI_MAJOR_VERSION = _get_kodi_major_version()
USE_INFOTAG = KODI_MAJOR_VERSION >= 20

########################

''' File-based cache to replace simplecache (which has threading issues on Kodi 21+)
'''
try:
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)
except OSError:
    pass


def _cache_filename(key):
    safe_key = hashlib.md5(str(key).encode()).hexdigest()
    return os.path.join(CACHE_PATH, safe_key + '.json')


def get_cache(key):
    if not CACHE_ENABLED:
        return None

    filepath = _cache_filename(CACHE_PREFIX + key)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            expires = data.get('_expires', 0)
            if expires > time.time():
                return data.get('_data')
            else:
                # Expired, remove file
                try:
                    os.remove(filepath)
                except OSError:
                    pass
    except Exception as error:
        log('Cache read error: %s' % error, DEBUG)

    return None


def write_cache(key, data, cache_time=336):
    if not data:
        return

    filepath = _cache_filename(CACHE_PREFIX + key)
    try:
        cache_entry = {
            '_data': data,
            '_expires': time.time() + (cache_time * 3600)
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cache_entry, f, ensure_ascii=False)
    except Exception as error:
        log('Cache write error: %s' % error, DEBUG)


def cache_cleanup(max_age_days=30):
    """Remove expired cache files older than max_age_days."""
    try:
        cutoff = time.time() - (max_age_days * 86400)
        for filename in os.listdir(CACHE_PATH):
            filepath = os.path.join(CACHE_PATH, filename)
            if os.path.isfile(filepath):
                if os.stat(filepath).st_mtime < cutoff:
                    os.remove(filepath)
    except Exception:
        pass


########################

def log(txt,loglevel=DEBUG,json_data=False,force=False):
    if force:
        loglevel = INFO

    if json_data:
        txt = json_prettyprint(txt)

    message = u'[ %s ] %s' % (ADDON_ID,txt)
    xbmc.log(msg=message, level=loglevel)


def format_currency(integer):
    try:
        integer = int(integer)
        if integer < 1:
            raise Exception

        return '{:,.0f}'.format(integer)

    except Exception:
        return ''


def sort_dict(items,key,reverse=False):
    ''' Dummy date to always add planned or rumored items at the end of the list
        if no release date is available yet.
    '''
    for item in items:
        if not item.get(key):
            if not reverse:
                item[key] = '2999-01-01'
            else:
                item[key] = '1900-01-01'

    return sorted(items, key=operator.itemgetter(key),reverse=reverse)


def remove_quotes(label):
    if not label:
        return ''

    if label.startswith("'") and label.endswith("'") and len(label) > 2:
        label = label[1:-1]
        if label.startswith('"') and label.endswith('"') and len(label) > 2:
            label = label[1:-1]

    return label


def get_date(date_time):
    date_time_obj = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    date_obj = date_time_obj.date()

    return date_obj


def execute(cmd):
    xbmc.executebuiltin(cmd)


def condition(condition):
    return xbmc.getCondVisibility(condition)


def busydialog(close=False):
    if not close and not condition('Window.IsVisible(busydialognocancel)'):
        execute('ActivateWindow(busydialognocancel)')
    elif close:
        execute('Dialog.Close(busydialognocancel)')


def textviewer(params):
    DIALOG.textviewer(remove_quotes(params.get('header', '')), remove_quotes(params.get('message', '')))


def winprop(key,value=None,clear=False,window_id=10000):
    window = xbmcgui.Window(window_id)

    if clear:
        window.clearProperty(key.replace('.json', '').replace('.bool', ''))

    elif value is not None:

        if key.endswith('.json'):
            key = key.replace('.json', '')
            value = json.dumps(value)

        elif key.endswith('.bool'):
            key = key.replace('.bool', '')
            value = 'true' if value else 'false'

        window.setProperty(key, value)

    else:
        result = window.getProperty(key.replace('.json', '').replace('.bool', ''))

        if result:
            if key.endswith('.json'):
                result = json.loads(result)
            elif key.endswith('.bool'):
                result = result in ('true', '1')

        return result


def date_year(value):
    if not value:
        return value

    try:
        dt = datetime.datetime.strptime(value[:10], '%Y-%m-%d')
        return str(dt.year)
    except Exception:
        pass

    return value


def date_format(value, date='short', scheme=None):
    if not value:
        return value

    try:
        if scheme:
            # Handle OMDB-style dates like "01 Jan 2020"
            dt = datetime.datetime.strptime(value.strip(), '%d %b %Y')
        else:
            dt = datetime.datetime.strptime(value[:10], '%Y-%m-%d')

        value = dt.strftime(xbmc.getRegion('date%s' % date))

    except Exception:
        pass

    return value


def date_delta(date):
    try:
        dt = datetime.datetime.strptime(date[:10], '%Y-%m-%d').date()
        return dt - datetime.date.today()
    except Exception:
        return datetime.timedelta(days=9999)


def date_weekday(date=None):
    try:
        weekdays = (xbmc.getLocalizedString(11), xbmc.getLocalizedString(12), xbmc.getLocalizedString(13), xbmc.getLocalizedString(14), xbmc.getLocalizedString(15), xbmc.getLocalizedString(16), xbmc.getLocalizedString(17))

        if date:
            if isinstance(date, str):
                dt = datetime.datetime.strptime(date[:10], '%Y-%m-%d').date()
            else:
                dt = date
        else:
            dt = datetime.date.today()

        weekday = dt.weekday()
        return weekdays[weekday], weekday

    except Exception:
        return '', ''


def utc_to_local(value):
    try:
        # Parse the ISO format UTC datetime
        if 'T' in value:
            value_clean = value.replace('Z', '+00:00')
            if '+' in value_clean[10:] or value_clean.endswith('+00:00'):
                dt_utc = datetime.datetime.fromisoformat(value_clean)
            else:
                dt_utc = datetime.datetime.fromisoformat(value_clean).replace(tzinfo=datetime.timezone.utc)
        else:
            dt_utc = datetime.datetime.strptime(value[:10], '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)

        # Convert to local time
        dt_local = dt_utc.astimezone()

        conv_date_str = dt_local.strftime('%Y-%m-%d')

        if xbmc.getRegion('time').startswith('%I'):
            conv_time_str = dt_local.strftime('%I:%M %p')
        else:
            conv_time_str = dt_local.strftime('%H:%M')

        return conv_date_str, conv_time_str

    except Exception:
        return value[:10] if len(value) >= 10 else value, ''


def get_bool(value,string='true'):
    try:
        if value.lower() == string:
            return True
        raise Exception

    except Exception:
        return False


def get_joined_items(item):
    if len(item) > 0:
        item = ' / '.join(item)
    else:
        item = ''
    return item


def get_first_item(item):
    if len(item) > 0:
        item = item[0]
    else:
        item = ''

    return item


def json_call(method,properties=None,sort=None,query_filter=None,limit=None,params=None,item=None,options=None,limits=None):
    json_string = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': {}}

    if properties is not None:
        json_string['params']['properties'] = properties

    if limit is not None:
        json_string['params']['limits'] = {'start': 0, 'end': int(limit)}

    if sort is not None:
        json_string['params']['sort'] = sort

    if query_filter is not None:
        json_string['params']['filter'] = query_filter

    if options is not None:
        json_string['params']['options'] = options

    if limits is not None:
        json_string['params']['limits'] = limits

    if item is not None:
        json_string['params']['item'] = item

    if params is not None:
        json_string['params'].update(params)

    json_string = json.dumps(json_string)
    result = xbmc.executeJSONRPC(json_string)
    return json.loads(result)


def json_prettyprint(string):
    return json.dumps(string, sort_keys=True, indent=4, separators=(',', ': '))


def urljoin(*args):
    ''' Joins given arguments into an url. Trailing but not leading slashes are
        stripped for each argument.
    '''
    arglist = [arg for arg in args if arg is not None]
    return '/'.join(map(lambda x: str(x).rstrip('/'), arglist))


def md5hash(value):
    value = str(value).encode()
    return hashlib.md5(value).hexdigest()


def set_video_info(list_item, info):
    """Apply video info to a ListItem using the modern InfoTagVideo API
    on Kodi 20+ (Nexus/Omega), falling back to the deprecated
    ListItem.setInfo() on older Kodi versions.

    Accepts the same dict format as the legacy ListItem.setInfo('video', ...).
    Unknown/unsupported keys are silently skipped to keep behaviour identical
    to the legacy call (which also tolerated unknowns).
    """
    if not USE_INFOTAG:
        # Legacy Kodi (< 20): use the old API.
        try:
            list_item.setInfo('video', info)
        except Exception:
            pass
        return

    # Modern Kodi (>= 20): use InfoTagVideo with explicit setters.
    try:
        tag = list_item.getVideoInfoTag()

        # Mapping: info-key -> (setter-name, optional-converter)
        setters = {
            'title':         ('setTitle', str),
            'originaltitle': ('setOriginalTitle', str),
            'sorttitle':     ('setSortTitle', str),
            'tvshowtitle':   ('setTvShowTitle', str),
            'plot':          ('setPlot', str),
            'plotoutline':   ('setPlotOutline', str),
            'tagline':       ('setTagLine', str),
            'mpaa':          ('setMpaa', str),
            'studio':        ('setStudios', lambda v: [v] if isinstance(v, str) else list(v)),
            'genre':         ('setGenres', lambda v: [v] if isinstance(v, str) else list(v)),
            'country':       ('setCountries', lambda v: [v] if isinstance(v, str) else list(v)),
            'director':      ('setDirectors', lambda v: [v] if isinstance(v, str) else list(v)),
            'writer':        ('setWriters', lambda v: [v] if isinstance(v, str) else list(v)),
            'premiered':     ('setPremiered', str),
            'firstaired':    ('setFirstAired', str),
            'status':        ('setTvShowStatus', str),
            'mediatype':     ('setMediaType', str),
            'imdbnumber':    ('setIMDBNumber', str),
            'trailer':       ('setTrailer', str),
        }

        for key, value in info.items():
            if value is None or value == '':
                continue
            if key in setters:
                setter_name, converter = setters[key]
                try:
                    getattr(tag, setter_name)(converter(value))
                except (TypeError, ValueError, AttributeError):
                    continue
            elif key == 'rating':
                try:
                    tag.setRating(float(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'votes':
                try:
                    tag.setVotes(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'duration':
                try:
                    tag.setDuration(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'playcount':
                try:
                    tag.setPlaycount(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'dbid':
                try:
                    tag.setDbId(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'year':
                try:
                    tag.setYear(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'season':
                try:
                    tag.setSeason(int(value))
                except (TypeError, ValueError):
                    continue
            elif key == 'episode':
                try:
                    tag.setEpisode(int(value))
                except (TypeError, ValueError):
                    continue
            # Unknown keys are silently skipped.

    except Exception:
        # If anything goes wrong with the modern API, fall back to legacy.
        try:
            list_item.setInfo('video', info)
        except Exception:
            pass
