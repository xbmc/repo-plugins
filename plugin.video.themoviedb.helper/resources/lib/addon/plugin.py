import re
import xbmc
import xbmcgui
import xbmcaddon
import hashlib
import traceback
from resources.lib.addon.constants import LANGUAGES


ADDON = xbmcaddon.Addon('plugin.video.themoviedb.helper')
ADDONPATH = ADDON.getAddonInfo('path')
PLUGINPATH = u'plugin://plugin.video.themoviedb.helper/'
ADDONDATA = 'special://profile/addon_data/plugin.video.themoviedb.helper/'

_addonlogname = '[plugin.video.themoviedb.helper]\n'
_debuglogging = ADDON.getSettingBool('debug_logging')


def format_name(cache_name, *args, **kwargs):
    # Define a type whitelist to avoiding adding non-basic types like classes to cache name
    permitted_types = (int, float, str, bool, bytes)
    for arg in args:
        if not isinstance(arg, permitted_types):
            continue
        cache_name = u'{}/{}'.format(cache_name, arg) if cache_name else u'{}'.format(arg)
    for key, value in sorted(kwargs.items()):
        if not isinstance(value, permitted_types):
            continue
        cache_name = u'{}&{}={}'.format(cache_name, key, value) if cache_name else u'{}={}'.format(key, value)
    return cache_name


def format_folderpath(path, content='videos', affix='return', info=None, play='PlayMedia'):
    if not path:
        return
    if info == 'play':
        return u'{}({})'.format(play, path)
    if xbmc.getCondVisibility("Window.IsMedia"):
        return u'Container.Update({})'.format(path)
    return u'ActivateWindow({},{},{})'.format(content, path, affix)


def reconfigure_legacy_params(**kwargs):
    if 'type' in kwargs:
        kwargs['tmdb_type'] = kwargs.pop('type')
    if kwargs.get('tmdb_type') in ['season', 'episode']:
        kwargs['tmdb_type'] = 'tv'
    return kwargs


def set_kwargattr(obj, kwargs):
    for k, v in kwargs.items():
        setattr(obj, k, v)


def md5hash(value):
    value = str(value).encode()
    return hashlib.md5(value).hexdigest()


def kodi_log(value, level=0):
    try:
        if isinstance(value, list):
            v = ''
            for i in value:
                v = u'{}{}'.format(v, i) if v else u'{}'.format(i)
            value = v
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        logvalue = u'{0}{1}'.format(_addonlogname, value)
        if level == 2 and _debuglogging:
            xbmc.log(logvalue, level=xbmc.LOGINFO)
        elif level == 1:
            xbmc.log(logvalue, level=xbmc.LOGINFO)
        else:
            xbmc.log(logvalue, level=xbmc.LOGDEBUG)
    except Exception as exc:
        xbmc.log(u'Logging Error: {}'.format(exc), level=xbmc.LOGINFO)


def kodi_traceback(exception, log_msg=None, notification=True, log_level=1):
    if notification:
        head = u'TheMovieDb Helper {}'.format(xbmc.getLocalizedString(257))
        xbmcgui.Dialog().notification(head, xbmc.getLocalizedString(2104))
    msg = u'Error Type: {0}\nError Contents: {1!r}'
    msg = msg.format(type(exception).__name__, exception.args)
    msg = [log_msg, '\n', msg, '\n'] if log_msg else [msg, '\n']
    try:
        kodi_log(msg + traceback.format_tb(exception.__traceback__), log_level)
    except Exception as exc:
        kodi_log(u'ERROR WITH TRACEBACK!\n{}\n{}'.format(exc, msg), log_level)


def get_language():
    if ADDON.getSettingInt('language'):
        return LANGUAGES[ADDON.getSettingInt('language')]
    return 'en-US'


def get_mpaa_prefix():
    if ADDON.getSettingString('mpaa_prefix'):
        return u'{} '.format(ADDON.getSettingString('mpaa_prefix'))
    return u''


CONVERSION_TABLE = {
    'media': {
        'movie': {'tmdb': 'movie', 'trakt': 'movie', 'ftv': 'movies'},
        'tvshow': {'tmdb': 'tv', 'trakt': 'show', 'ftv': 'tv'},
        'season': {'tmdb': 'season', 'trakt': 'season', 'ftv': 'tv'},
        'episode': {'tmdb': 'episode', 'trakt': 'episode', 'ftv': 'tv'},
        'actor': {'tmdb': 'person'},
        'director': {'tmdb': 'person'},
        'set': {'tmdb': 'collection'}
    },
    'trakt': {
        'movie': {'tmdb': 'movie'},
        'show': {'tmdb': 'tv'},
        'season': {'tmdb': 'season'},
        'episode': {'tmdb': 'episode'},
        'person': {'tmdb': 'person'}
    },
    'tmdb': {
        'movie': {'plural': lambda: xbmc.getLocalizedString(342), 'container': 'movies', 'trakt': 'movie', 'dbtype': 'movie'},
        'tv': {'plural': lambda: xbmc.getLocalizedString(20343), 'container': 'tvshows', 'trakt': 'show', 'dbtype': 'tvshow'},
        'person': {'plural': lambda: ADDON.getLocalizedString(32172), 'container': 'actors', 'dbtype': 'video'},  # Actors needs video type for info dialog
        'collection': {'plural': lambda: ADDON.getLocalizedString(32187), 'container': 'sets', 'dbtype': 'set'},
        'review': {'plural': lambda: ADDON.getLocalizedString(32188)},
        'keyword': {'plural': lambda: xbmc.getLocalizedString(21861), 'dbtype': 'keyword'},
        'network': {'plural': lambda: ADDON.getLocalizedString(32189), 'container': 'studios', 'dbtype': 'studio'},
        'studio': {'plural': lambda: ADDON.getLocalizedString(32190), 'container': 'studios', 'dbtype': 'studio'},
        'company': {'plural': lambda: ADDON.getLocalizedString(32360), 'container': 'studios', 'dbtype': 'studio'},
        'image': {'plural': lambda: ADDON.getLocalizedString(32191), 'container': 'images'},
        'genre': {'plural': lambda: xbmc.getLocalizedString(135), 'container': 'genres', 'dbtype': 'genre'},
        'season': {'plural': lambda: xbmc.getLocalizedString(33054), 'container': 'seasons', 'trakt': 'season', 'dbtype': 'season'},
        'episode': {'plural': lambda: xbmc.getLocalizedString(20360), 'container': 'episodes', 'trakt': 'episode', 'dbtype': 'episode'},
        'video': {'plural': lambda: xbmc.getLocalizedString(10025), 'container': 'videos', 'dbtype': 'video'},
        'both': {'plural': lambda: ADDON.getLocalizedString(32365), 'trakt': 'both'}
    }
}


def _convert_types(base, key, output):
    info = CONVERSION_TABLE.get(base, {}).get(key, {}).get(output) or ''
    return info() if callable(info) else info


def convert_media_type(media_type, output='tmdb', parent_type=False, strip_plural=False):
    if strip_plural:  # Strip trailing "s" from container_content to convert to media_type
        media_type = re.sub('s$', '', media_type)
    if parent_type and media_type in ['season', 'episode']:
        media_type = 'tvshow'
    return _convert_types('media', media_type, output)


def convert_trakt_type(trakt_type, output='tmdb'):
    return _convert_types('trakt', trakt_type, output)


def convert_type(tmdb_type, output, season=None, episode=None):
    if output == 'library':
        if tmdb_type == 'image':
            return 'pictures'
        return 'video'
    if tmdb_type == 'tv' and season is not None:
        tmdb_type == 'episode' if episode is not None else 'season'
    return _convert_types('tmdb', tmdb_type, output)
