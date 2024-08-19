import re
import xbmc
import jurialmunkey.plugin
import jurialmunkey.parser
from tmdbhelper.lib.addon.consts import LANGUAGES
""" Top level module only import constants """


KODIPLUGIN = jurialmunkey.plugin.KodiPlugin('plugin.video.themoviedb.helper')
ADDON = KODIPLUGIN._addon
ADDONPATH = KODIPLUGIN._addon_path
ADDONNAME = KODIPLUGIN._addon_name
ADDONDATA = 'special://profile/addon_data/plugin.video.themoviedb.helper/'
PLUGINPATH = u'plugin://plugin.video.themoviedb.helper/'

get_setting = KODIPLUGIN.get_setting
set_setting = KODIPLUGIN.set_setting
get_localized = KODIPLUGIN.get_localized

encode_url = jurialmunkey.parser.EncodeURL(u'plugin://plugin.video.themoviedb.helper/').encode_url

executebuiltin = xbmc.executebuiltin
get_condvisibility = xbmc.getCondVisibility
get_infolabel = xbmc.getInfoLabel
format_name = jurialmunkey.plugin.format_name
format_folderpath = jurialmunkey.plugin.format_folderpath
set_kwargattr = jurialmunkey.plugin.set_kwargattr


def get_plugin_category(info_model, plural=''):
    plugin_category = info_model.get('plugin_category')
    if not plugin_category:
        return
    localized = get_localized(info_model['localized']) if 'localized' in info_model else ''
    return plugin_category.format(localized=localized, plural=plural)


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
        'video': {'plural': lambda: get_localized(10025), 'container': 'videos', 'dbtype': 'video'}
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


def convert_type(tmdb_type, output, season=None, episode=None, items=None):
    if output == 'library':
        if tmdb_type == 'image':
            return 'pictures'
        return 'video'
    if tmdb_type == 'both':
        if output == 'plural':
            return get_localized(32365)
        if output == 'trakt':
            return 'both'
        if not items:
            return ''
        dbtypes = {}
        for i in items:
            try:
                dbtype = i['infolabels']['mediatype']
            except KeyError:
                continue
            if not dbtype:
                continue
            dbtypes[dbtype] = dbtypes.get(dbtype, 0) + 1
        try:
            dbtype = max(dbtypes, key=dbtypes.get)
        except ValueError:
            return ''
        tmdb_type = convert_media_type(dbtype)
    if tmdb_type == 'tv' and season is not None:
        tmdb_type = 'episode' if episode is not None else 'season'
    return _convert_types('tmdb', tmdb_type, output)
