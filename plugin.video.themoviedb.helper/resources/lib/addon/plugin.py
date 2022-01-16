import re
import xbmc
from xbmcaddon import Addon as KodiAddon
from resources.lib.addon.consts import LANGUAGES
""" Top level module only import constants """


ADDON = KodiAddon('plugin.video.themoviedb.helper')
ADDONPATH = ADDON.getAddonInfo('path')
ADDONNAME = ADDON.getAddonInfo('name')
PLUGINPATH = u'plugin://plugin.video.themoviedb.helper/'
ADDONDATA = 'special://profile/addon_data/plugin.video.themoviedb.helper/'
ADDONGETSETTINGROUTE = {
    'bool': ADDON.getSettingBool,
    'int': ADDON.getSettingInt,
    'str': ADDON.getSettingString
}
ADDONSETSETTINGROUTE = {
    'bool': ADDON.setSettingBool,
    'int': ADDON.setSettingInt,
    'str': ADDON.setSettingString
}


_executebuiltin = xbmc.executebuiltin
_getcondvisibility = xbmc.getCondVisibility
_getinfolabel = xbmc.getInfoLabel
_getxbmclocalized = xbmc.getLocalizedString
_getaddonlocalized = ADDON.getLocalizedString


def executebuiltin(builtin):
    _executebuiltin(builtin)


def get_condvisibility(condition):
    return _getcondvisibility(condition)


def get_infolabel(infolabel):
    return _getinfolabel(infolabel)


def get_setting(setting, mode='bool'):
    return ADDONGETSETTINGROUTE[mode](setting)


def set_setting(setting, data, mode='bool'):
    return ADDONSETSETTINGROUTE[mode](setting, data)


def get_localized(localize_int=0):
    if localize_int < 30000 or localize_int >= 33000:
        return _getxbmclocalized(localize_int)
    return _getaddonlocalized(localize_int)


def get_plugin_category(info_model, plural=''):
    plugin_category = info_model.get('plugin_category')
    if not plugin_category:
        return
    localized = get_localized(info_model['localized']) if 'localized' in info_model else ''
    return plugin_category.format(localized=localized, plural=plural)


def format_name(cache_name, *args, **kwargs):
    # Define a type whitelist to avoiding adding non-basic types like classes to cache name
    permitted_types = (int, float, str, bool, bytes)
    for arg in args:
        if not isinstance(arg, permitted_types):
            continue
        cache_name = f'{cache_name}/{arg}' if cache_name else f'{arg}'
    for key, value in sorted(kwargs.items()):
        if not isinstance(value, permitted_types):
            continue
        cache_name = f'{cache_name}&{key}={value}' if cache_name else f'{key}={value}'
    return cache_name


def format_folderpath(path, content='videos', affix='return', info=None, play='PlayMedia'):
    if not path:
        return
    if info == 'play':
        return f'{play}({path})'
    if _getcondvisibility("Window.IsMedia") and _getinfolabel("System.CurrentWindow").lower() == content:
        return f'Container.Update({path})'
    return f'ActivateWindow({content},{path},{affix})'


def set_kwargattr(obj, kwargs):
    for k, v in kwargs.items():
        setattr(obj, k, v)


def get_language():
    if ADDON.getSettingInt('language'):
        return LANGUAGES[ADDON.getSettingInt('language')]
    return 'en-US'


def get_mpaa_prefix():
    if ADDON.getSettingString('mpaa_prefix'):
        return f'{ADDON.getSettingString("mpaa_prefix")} '
    return ''


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
        'movie': {'plural': lambda: get_localized(342), 'container': 'movies', 'trakt': 'movie', 'dbtype': 'movie'},
        'tv': {'plural': lambda: get_localized(20343), 'container': 'tvshows', 'trakt': 'show', 'dbtype': 'tvshow'},
        'person': {'plural': lambda: get_localized(32172), 'container': 'actors', 'dbtype': 'video'},  # Actors needs video type for info dialog
        'collection': {'plural': lambda: get_localized(32187), 'container': 'sets', 'dbtype': 'set'},
        'review': {'plural': lambda: get_localized(32188)},
        'keyword': {'plural': lambda: get_localized(21861), 'dbtype': 'keyword'},
        'network': {'plural': lambda: get_localized(32189), 'container': 'studios', 'dbtype': 'studio'},
        'studio': {'plural': lambda: get_localized(32190), 'container': 'studios', 'dbtype': 'studio'},
        'company': {'plural': lambda: get_localized(32360), 'container': 'studios', 'dbtype': 'studio'},
        'image': {'plural': lambda: get_localized(32191), 'container': 'images'},
        'genre': {'plural': lambda: get_localized(135), 'container': 'genres', 'dbtype': 'genre'},
        'season': {'plural': lambda: get_localized(33054), 'container': 'seasons', 'trakt': 'season', 'dbtype': 'season'},
        'episode': {'plural': lambda: get_localized(20360), 'container': 'episodes', 'trakt': 'episode', 'dbtype': 'episode'},
        'video': {'plural': lambda: get_localized(10025), 'container': 'videos', 'dbtype': 'video'},
        'both': {'plural': lambda: get_localized(32365), 'trakt': 'both'}
    }
}


def _convert_types(base, key, output):
    try:
        info = CONVERSION_TABLE[base][key][output] or ''
    except KeyError:
        return ''
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
