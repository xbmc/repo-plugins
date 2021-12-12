# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import sys
import xbmc
import xbmcvfs
import xbmcgui
from json import dumps
from resources.lib.kodi.library import add_to_library
from resources.lib.kodi.userlist import monitor_userlist, library_autoupdate
from resources.lib.kodi.rpc import get_jsonrpc
from resources.lib.files.downloader import Downloader
from resources.lib.files.utils import dumps_to_file, validify_filename
from resources.lib.addon.window import get_property
from resources.lib.addon.plugin import ADDON, reconfigure_legacy_params, kodi_log, format_folderpath, convert_type
from resources.lib.addon.decorators import busy_dialog
from resources.lib.addon.parser import encode_url
from resources.lib.container.basedir import get_basedir_details
from resources.lib.fanarttv.api import FanartTV
from resources.lib.tmdb.api import TMDb
from resources.lib.trakt.api import TraktAPI, get_sort_methods
from resources.lib.omdb.api import OMDb
from resources.lib.script.sync import sync_trakt_item
from resources.lib.window.manager import WindowManager
from resources.lib.player.players import Players
from resources.lib.player.configure import configure_players
from resources.lib.monitor.images import ImageFunctions
from resources.lib.container.listitem import ListItem


# Get TMDb ID decorator
def get_tmdb_id(func):
    def wrapper(*args, **kwargs):
        with busy_dialog():
            if not kwargs.get('tmdb_id'):
                kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)
        return func(*args, **kwargs)
    return wrapper


def map_kwargs(mapping={}):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if k in kwargs:
                    kwargs[v] = kwargs.pop(k, None)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_in_kwargs(mapping={}):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if kwargs.get(k) not in v:
                    return
            return func(*args, **kwargs)
        return wrapper
    return decorator


def play_media(**kwargs):
    with busy_dialog():
        kodi_log(['lib.script.router - attempting to play\n', kwargs.get('play_media')], 1)
        xbmc.executebuiltin(u'PlayMedia({})'.format(kwargs.get('play_media')))


def run_plugin(**kwargs):
    with busy_dialog():
        kodi_log(['lib.script.router - attempting to play\n', kwargs.get('run_plugin')], 1)
        xbmc.executebuiltin(u'RunPlugin({})'.format(kwargs.get('run_plugin')))


def container_refresh():
    xbmc.executebuiltin('Container.Refresh')
    xbmc.executebuiltin('UpdateLibrary(video,/fake/path/to/force/refresh/on/home)')


def delete_cache(delete_cache, **kwargs):
    d = {
        'TMDb': lambda: TMDb(),
        'Trakt': lambda: TraktAPI(),
        'FanartTV': lambda: FanartTV(),
        'OMDb': lambda: OMDb()}
    if delete_cache == 'select':
        m = [i for i in d]
        x = xbmcgui.Dialog().contextmenu([ADDON.getLocalizedString(32387).format(i) for i in m])
        if x == -1:
            return
        delete_cache = m[x]
    z = d.get(delete_cache)
    if not z:
        return
    if not xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32387).format(delete_cache), ADDON.getLocalizedString(32388).format(delete_cache)):
        return
    with busy_dialog():
        z()._cache.ret_cache()._do_delete()
    xbmcgui.Dialog().ok(ADDON.getLocalizedString(32387).format(delete_cache), ADDON.getLocalizedString(32389))


@map_kwargs({'play': 'tmdb_type'})
@get_tmdb_id
def play_external(**kwargs):
    kodi_log(['lib.script.router - attempting to play\n', kwargs], 1)
    Players(**kwargs).play()


# def add_to_queue(episodes, clear_playlist=False, play_next=False):
#     if not episodes:
#         return
#     playlist = xbmc.PlayList(1)
#     if clear_playlist:
#         playlist.clear()
#     for i in episodes:
#         li = ListItem(**i)
#         li.set_params_reroute()
#         playlist.add(li.get_url(), li.get_listitem())
#     if play_next:
#         xbmc.Player().play(playlist)


# def play_season(**kwargs):
#     with busy_dialog():
#         if not kwargs.get('tmdb_id'):
#             kwargs['tmdb_type'] = 'tv'
#             kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)
#         if not kwargs['tmdb_id']:
#             return
#         add_to_queue(
#             TMDb().get_episode_list(tmdb_id=kwargs['tmdb_id'], season=kwargs['play_season']),
#             clear_playlist=True, play_next=True)


def split_value(split_value, separator=None, **kwargs):
    split_value = split_value or ''
    for x, i in enumerate(split_value.split(separator or ' / ')):
        name = u'{}.{}'.format(kwargs.get('property') or 'TMDbHelper.Split', x)
        get_property(name, set_property=i, prefix=-1)


@is_in_kwargs({'tmdb_type': ['movie', 'tv']})
@get_tmdb_id
def sync_trakt(**kwargs):
    sync_trakt_item(
        trakt_type=convert_type(kwargs['tmdb_type'], 'trakt', season=kwargs.get('season'), episode=kwargs.get('episode')),
        unique_id=kwargs['tmdb_id'],
        season=kwargs.get('season'),
        episode=kwargs.get('episode'),
        id_type='tmdb')


def _get_ftv_id(**kwargs):
    details = refresh_details(confirm=False, **kwargs)
    if not details:
        return
    return ListItem(**details).get_ftv_id()


def manage_artwork(ftv_id=None, ftv_type=None, **kwargs):
    if not ftv_type:
        return
    if not ftv_id:
        ftv_id = _get_ftv_id(**kwargs)
    if not ftv_id:
        return
    FanartTV().manage_artwork(ftv_id, ftv_type)


@get_tmdb_id
def related_lists(tmdb_id=None, tmdb_type=None, season=None, episode=None, container_update=True, include_play=False, **kwargs):
    if not tmdb_id or not tmdb_type:
        return
    items = get_basedir_details(tmdb_type=tmdb_type, tmdb_id=tmdb_id, season=season, episode=episode, include_play=include_play)
    if not items or len(items) <= 1:
        return
    choice = xbmcgui.Dialog().contextmenu([i.get('label') for i in items])
    if choice == -1:
        return
    item = items[choice]
    params = item.get('params')
    if not params:
        return
    item['params']['tmdb_id'] = tmdb_id
    item['params']['tmdb_type'] = tmdb_type
    if not container_update:
        return item
    path = format_folderpath(
        path=encode_url(path=item.get('path'), **item.get('params')),
        info=item['params']['info'], play='RunPlugin',  # Use RunPlugin to avoid window manager info dialog crash with Browse method
        content='pictures' if item['params']['info'] in ['posters', 'fanart'] else 'videos')
    xbmc.executebuiltin(path)


def update_players():
    players_url = ADDON.getSettingString('players_url')
    players_url = xbmcgui.Dialog().input(ADDON.getLocalizedString(32313), defaultt=players_url)
    if not xbmcgui.Dialog().yesno(
            ADDON.getLocalizedString(32032),
            ADDON.getLocalizedString(32314).format(players_url)):
        return
    ADDON.setSettingString('players_url', players_url)
    downloader = Downloader(
        extract_to='special://profile/addon_data/plugin.video.themoviedb.helper/players',
        download_url=players_url)
    downloader.get_extracted_zip()


@get_tmdb_id
def refresh_details(tmdb_id=None, tmdb_type=None, season=None, episode=None, confirm=True, **kwargs):
    if not tmdb_id or not tmdb_type:
        return
    with busy_dialog():
        details = TMDb().get_details(tmdb_type, tmdb_id, season, episode, cache_refresh=True)
    if details and confirm:
        xbmcgui.Dialog().ok('TMDbHelper', ADDON.getLocalizedString(32234).format(tmdb_type, tmdb_id))
        container_refresh()
    return details


def kodi_setting(kodi_setting, **kwargs):
    method = "Settings.GetSettingValue"
    params = {"setting": kodi_setting}
    response = get_jsonrpc(method, params)
    get_property(
        name=kwargs.get('property') or 'TMDbHelper.KodiSetting',
        set_property=u'{}'.format(response.get('result', {}).get('value', '')))


def user_list(user_list, user_slug=None, **kwargs):
    user_slug = user_slug or 'me'
    if not user_slug or not user_list:
        return
    add_to_library(info='trakt', user_slug=user_slug, list_slug=user_list, confirm=True, allow_update=True, busy_spinner=True)


def delete_list(delete_list, **kwargs):
    if not xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32358), ADDON.getLocalizedString(32357).format(delete_list)):
        return
    TraktAPI().delete_response('users/me/lists', delete_list)
    container_refresh()


def rename_list(rename_list, **kwargs):
    name = xbmcgui.Dialog().input(ADDON.getLocalizedString(32359))
    if not name:
        return
    TraktAPI().post_response('users/me/lists', rename_list, postdata={'name': name}, response_method='put')
    container_refresh()


def like_list(like_list, user_slug=None, delete=False, **kwargs):
    user_slug = user_slug or 'me'
    if not user_slug or not like_list:
        return
    TraktAPI().like_userlist(user_slug=user_slug, list_slug=like_list, confirmation=True, delete=delete)
    if not delete:
        return
    container_refresh()


def set_defaultplayer(**kwargs):
    tmdb_type = kwargs.get('set_defaultplayer')
    setting_name = 'default_player_movies' if tmdb_type == 'movie' else 'default_player_episodes'
    default_player = Players(tmdb_type).select_player(detailed=True, clear_player=True)
    if not default_player:
        return
    if not default_player.get('file') or not default_player.get('mode'):
        return ADDON.setSettingString(setting_name, '')
    ADDON.setSettingString(setting_name, u'{} {}'.format(default_player['file'], default_player['mode']))


def blur_image(blur_image=None, **kwargs):
    blur_img = ImageFunctions(method='blur', artwork=blur_image)
    blur_img.setName('blur_img')
    blur_img.start()


def image_colors(image_colors=None, **kwargs):
    image_colors = ImageFunctions(method='colors', artwork=image_colors)
    image_colors.setName('image_colors')
    image_colors.start()


def library_update(**kwargs):
    if kwargs.get('force') == 'select':
        choice = xbmcgui.Dialog().yesno(
            ADDON.getLocalizedString(32391),
            ADDON.getLocalizedString(32392),
            yeslabel=ADDON.getLocalizedString(32393),
            nolabel=ADDON.getLocalizedString(32394))
        if choice == -1:
            return
        kwargs['force'] = True if choice else False
    library_autoupdate(
        list_slugs=kwargs.get('list_slug', None),
        user_slugs=kwargs.get('user_slug', None),
        busy_spinner=True if kwargs.get('busy_dialog', False) else False,
        force=kwargs.get('force', False))


def log_request(**kwargs):
    with busy_dialog():
        kwargs['response'] = None
        if not kwargs.get('url'):
            kwargs['url'] = xbmcgui.Dialog().input('URL')
        if not kwargs['url']:
            return
        if kwargs.get('log_request').lower() == 'trakt':
            kwargs['response'] = TraktAPI().get_response_json(kwargs['url'])
        else:
            kwargs['response'] = TMDb().get_response_json(kwargs['url'])
        if not kwargs['response']:
            xbmcgui.Dialog().ok(kwargs['log_request'].capitalize(), u'{}\nNo Response!'.format(kwargs['url']))
            return
        filename = validify_filename(u'{}_{}.json'.format(kwargs['log_request'], kwargs['url']))
        dumps_to_file(kwargs, 'log_request', filename)
        xbmcgui.Dialog().ok(kwargs['log_request'].capitalize(), u'[B]{}[/B]\n\n{}\n{}\n{}'.format(
            kwargs['url'], xbmcvfs.translatePath('special://profile/addon_data/'),
            'plugin.video.themoviedb.helper/log_request', filename))
        xbmcgui.Dialog().textviewer(filename, dumps(kwargs['response'], indent=2))


def sort_list(**kwargs):
    sort_methods = get_sort_methods() if kwargs['info'] == 'trakt_userlist' else get_sort_methods(True)
    x = xbmcgui.Dialog().contextmenu([i['name'] for i in sort_methods])
    if x == -1:
        return
    for k, v in sort_methods[x]['params'].items():
        kwargs[k] = v
    xbmc.executebuiltin(format_folderpath(encode_url(**kwargs)))


class Script(object):
    def __init__(self):
        self.params = {}
        for arg in sys.argv[1:]:
            if '=' in arg:
                key, value = arg.split('=', 1)
                self.params[key] = value.strip('\'').strip('"') if value else None
            else:
                self.params[arg] = True
        self.params = reconfigure_legacy_params(**self.params)

    routing_table = {
        'authenticate_trakt': lambda **kwargs: TraktAPI(force=True),
        'revoke_trakt': lambda **kwargs: TraktAPI().logout(),
        'split_value': lambda **kwargs: split_value(**kwargs),
        'kodi_setting': lambda **kwargs: kodi_setting(**kwargs),
        'sync_trakt': lambda **kwargs: sync_trakt(**kwargs),
        'manage_artwork': lambda **kwargs: manage_artwork(**kwargs),
        'refresh_details': lambda **kwargs: refresh_details(**kwargs),
        'related_lists': lambda **kwargs: related_lists(**kwargs),
        'user_list': lambda **kwargs: user_list(**kwargs),
        'like_list': lambda **kwargs: like_list(**kwargs),
        'delete_list': lambda **kwargs: delete_list(**kwargs),
        'rename_list': lambda **kwargs: rename_list(**kwargs),
        'blur_image': lambda **kwargs: blur_image(**kwargs),
        'image_colors': lambda **kwargs: image_colors(**kwargs),
        'monitor_userlist': lambda **kwargs: monitor_userlist(),
        'update_players': lambda **kwargs: update_players(),
        'set_defaultplayer': lambda **kwargs: set_defaultplayer(**kwargs),
        'configure_players': lambda **kwargs: configure_players(**kwargs),
        'library_autoupdate': lambda **kwargs: library_update(**kwargs),
        # 'play_season': lambda **kwargs: play_season(**kwargs),
        'play_media': lambda **kwargs: play_media(**kwargs),
        'run_plugin': lambda **kwargs: run_plugin(**kwargs),
        'log_request': lambda **kwargs: log_request(**kwargs),
        'delete_cache': lambda **kwargs: delete_cache(**kwargs),
        'play': lambda **kwargs: play_external(**kwargs),
        'add_path': lambda **kwargs: WindowManager(**kwargs).router(),
        'add_query': lambda **kwargs: WindowManager(**kwargs).router(),
        'close_dialog': lambda **kwargs: WindowManager(**kwargs).router(),
        'reset_path': lambda **kwargs: WindowManager(**kwargs).router(),
        'call_id': lambda **kwargs: WindowManager(**kwargs).router(),
        'call_path': lambda **kwargs: WindowManager(**kwargs).router(),
        'call_update': lambda **kwargs: WindowManager(**kwargs).router()
    }

    def router(self):
        if not self.params:
            return
        if self.params.get('restart_service'):
            # Only do the import here because this function only for debugging purposes
            from resources.lib.monitor.service import restart_service_monitor
            return restart_service_monitor()

        routes_available = set(self.routing_table.keys())
        params_given = set(self.params.keys())
        route_taken = set.intersection(routes_available, params_given).pop()
        kodi_log(['lib.script.router.Script - route_taken\t', route_taken], 0)
        return self.routing_table[route_taken](**self.params)
