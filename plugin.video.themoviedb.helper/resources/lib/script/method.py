# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
def map_kwargs(mapping={}):
    """ Decorator to remap kwargs key names """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if k in kwargs:
                    kwargs[v] = kwargs.pop(k, None)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_in_kwargs(mapping={}):
    """ Decorator to check that kwargs values match allowlist before running
    Accepts a dictionary of {kwarg: [allowlist]} key value pairs
    Decorated method is not run if kwargs.get(kwarg) not in [allowlist]
    Optionally can use {kwarg: True} to check kwarg exists and has any value
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for k, v in mapping.items():
                if v is True:
                    if kwargs.get(k) is None:
                        return
                else:
                    if kwargs.get(k) not in v:
                        return
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_tmdb_id(func):
    """ Decorator to get tmdb_id if not in kwargs """
    def wrapper(*args, **kwargs):
        from resources.lib.addon.dialog import BusyDialog
        from resources.lib.api.tmdb.api import TMDb
        with BusyDialog():
            if not kwargs.get('tmdb_id'):
                kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)
                if not kwargs['tmdb_id']:
                    return
        return func(*args, **kwargs)
    return wrapper


def choose_tmdb_id(func):
    """ Decorator to get tmdb_id if not in kwargs """
    def wrapper(*args, **kwargs):
        if kwargs.get('tmdb_id'):
            return func(*args, **kwargs)

        from xbmcgui import Dialog, ListItem
        from resources.lib.addon.dialog import BusyDialog
        from resources.lib.api.tmdb.api import TMDb
        from resources.lib.api.tmdb.mapping import get_imagepath_poster

        if kwargs.get('query'):
            with BusyDialog():
                response = TMDb().get_request_sc('search', kwargs['tmdb_type'], query=kwargs['query'])
            if not response or not response.get('results'):
                return

            items = []
            for i in response['results']:
                li = ListItem(
                    i.get('title') or i.get('name'),
                    i.get('release_date') or i.get('first_air_date'))
                li.setArt({'icon': get_imagepath_poster(i.get('poster_path'))})
                items.append(li)

            x = Dialog().select(kwargs['query'], items, useDetails=True)
            if x == -1:
                return
            kwargs['tmdb_id'] = response['results'][x].get('id')

        else:
            with BusyDialog():
                kwargs['tmdb_id'] = TMDb().get_tmdb_id(**kwargs)

        if not kwargs['tmdb_id']:
            return

        return func(*args, **kwargs)
    return wrapper


def container_refresh():
    from resources.lib.addon.tmdate import set_timestamp
    from resources.lib.addon.window import get_property
    from resources.lib.addon.plugin import executebuiltin
    executebuiltin('Container.Refresh')
    get_property('Widgets.Reload', set_property=f'{set_timestamp(0, True)}')


def split_value(split_value, separator=None, **kwargs):
    """ Split string values and output to window properties """
    from resources.lib.addon.window import get_property
    if not split_value:
        return
    v = f'{split_value}'
    s = separator or ' / '
    p = kwargs.get("property") or "TMDbHelper.Split"
    for x, i in enumerate(v.split(s)):
        get_property(f'{p}.{x}', set_property=i, prefix=-1)


def kodi_setting(kodi_setting, **kwargs):
    """ Get Kodi setting value and output to window property """
    from resources.lib.api.kodi.rpc import get_jsonrpc
    from resources.lib.addon.window import get_property
    method = "Settings.GetSettingValue"
    params = {"setting": kodi_setting}
    response = get_jsonrpc(method, params)
    get_property(
        name=kwargs.get('property') or 'TMDbHelper.KodiSetting',
        set_property=f'{response.get("result", {}).get("value", "")}')


@is_in_kwargs({'tmdb_type': ['movie', 'tv']})
@get_tmdb_id
def sync_trakt(tmdb_type=None, tmdb_id=None, season=None, episode=None, **kwargs):
    """ Open sync trakt menu for item """
    from resources.lib.script.sync import sync_trakt_item
    from resources.lib.addon.plugin import convert_type
    trakt_type = convert_type(tmdb_type, 'trakt', season=season, episode=episode)
    sync_trakt_item(trakt_type=trakt_type, unique_id=tmdb_id, season=season, episode=episode, id_type='tmdb')


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def manage_artwork(tmdb_id=None, tmdb_type=None, season=None, **kwargs):
    from resources.lib.items.builder import ItemBuilder
    ItemBuilder().manage_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def select_artwork(tmdb_id=None, tmdb_type=None, season=None, **kwargs):
    from resources.lib.items.builder import ItemBuilder
    ItemBuilder().select_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def refresh_details(tmdb_id=None, tmdb_type=None, season=None, episode=None, confirm=True, **kwargs):
    from xbmcgui import Dialog
    from resources.lib.items.builder import ItemBuilder
    from resources.lib.addon.dialog import BusyDialog
    from resources.lib.addon.plugin import get_localized
    with BusyDialog():
        details = ItemBuilder().get_item(tmdb_type, tmdb_id, season, episode, cache_refresh=True) or {}
        details = details.get('listitem')
    if details and confirm:
        Dialog().ok('TMDbHelper', get_localized(32234).format(tmdb_type, tmdb_id))
        container_refresh()
    return details


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def related_lists(tmdb_id=None, tmdb_type=None, season=None, episode=None, container_update=True, include_play=False, **kwargs):
    from xbmcgui import Dialog
    from resources.lib.items.basedir import get_basedir_details
    from resources.lib.addon.plugin import format_folderpath
    from resources.lib.addon.parser import encode_url
    from resources.lib.addon.plugin import executebuiltin
    items = get_basedir_details(tmdb_type=tmdb_type, tmdb_id=tmdb_id, season=season, episode=episode, include_play=include_play)
    if not items or len(items) <= 1:
        return
    choice = Dialog().contextmenu([i.get('label') for i in items])
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
        info=item['params']['info'],
        play='RunPlugin',  # Use RunPlugin to avoid window manager info dialog crash with Browse method
        content='pictures' if item['params']['info'] in ['posters', 'fanart'] else 'videos')
    executebuiltin('Dialog.Close(busydialog)')  # Kill modals because prevents ActivateWindow
    executebuiltin(path)


@is_in_kwargs({'tmdb_type': ['movie', 'tv']})
@choose_tmdb_id
def add_to_library(tmdb_type=None, tmdb_id=None, **kwargs):
    from resources.lib.update.library import add_to_library
    add_to_library(info=tmdb_type, tmdb_id=tmdb_id)


@is_in_kwargs({'user_list': True})
def user_list(user_list=None, user_slug=None, **kwargs):
    from resources.lib.update.library import add_to_library
    user_slug = user_slug or 'me'
    add_to_library(info='trakt', user_slug=user_slug, list_slug=user_list, confirm=True, allow_update=True, busy_spinner=True)


@is_in_kwargs({'like_list': True})
def like_list(like_list=None, user_slug=None, delete=False, **kwargs):
    from resources.lib.api.trakt.api import TraktAPI
    user_slug = user_slug or 'me'
    TraktAPI().like_userlist(user_slug=user_slug, list_slug=like_list, confirmation=True, delete=delete)
    if not delete:
        return
    container_refresh()


@is_in_kwargs({'delete_list': True})
def delete_list(delete_list=None, **kwargs):
    from xbmcgui import Dialog
    from resources.lib.api.trakt.api import TraktAPI
    from resources.lib.addon.plugin import get_localized
    if not Dialog().yesno(get_localized(32358), get_localized(32357).format(delete_list)):
        return
    TraktAPI().delete_response('users/me/lists', delete_list)
    container_refresh()


@is_in_kwargs({'rename_list': True})
def rename_list(rename_list=None, **kwargs):
    from xbmcgui import Dialog
    from resources.lib.api.trakt.api import TraktAPI
    from resources.lib.addon.plugin import get_localized
    name = Dialog().input(get_localized(32359))
    if not name:
        return
    TraktAPI().post_response('users/me/lists', rename_list, postdata={'name': name}, response_method='put')
    container_refresh()


def blur_image(blur_image=None, **kwargs):
    from resources.lib.monitor.images import ImageFunctions
    blur_img = ImageFunctions(method='blur', artwork=blur_image)
    blur_img.setName('blur_img')
    blur_img.start()


def image_colors(image_colors=None, **kwargs):
    from resources.lib.monitor.images import ImageFunctions
    image_colors = ImageFunctions(method='colors', artwork=image_colors)
    image_colors.setName('image_colors')
    image_colors.start()


def provider_allowlist():
    from xbmcgui import Dialog
    from resources.lib.api.tmdb.api import TMDb
    from resources.lib.addon.plugin import get_localized, get_setting, set_setting
    tmdb_api = TMDb()

    def _get_available_providers():
        available_providers = set()
        for tmdb_type in ['movie', 'tv']:
            results = tmdb_api.get_request_lc('watch/providers', tmdb_type, watch_region=tmdb_api.iso_country).get('results')
            if not results:
                continue
            available_providers |= {i.get('provider_name') for i in results}
        return available_providers

    available_providers = _get_available_providers()
    if not available_providers:
        return
    available_providers = sorted(available_providers)

    provider_allowlist = get_setting('provider_allowlist', 'str')
    provider_allowlist = provider_allowlist.split(' | ') if provider_allowlist else []
    preselected = [x for x, i in enumerate(available_providers) if not provider_allowlist or i in provider_allowlist]
    indices = Dialog().multiselect(get_localized(32437), available_providers, preselect=preselected)
    if indices is None:
        return

    selected_providers = [available_providers[x] for x in indices]
    if not selected_providers:
        return
    set_setting('provider_allowlist', ' | '.join(selected_providers), 'str')
    Dialog().ok(get_localized(32438), get_localized(32439))


def update_players():
    from xbmcgui import Dialog
    from resources.lib.files.downloader import Downloader
    from resources.lib.addon.plugin import set_setting
    from resources.lib.addon.plugin import get_setting
    from resources.lib.addon.plugin import get_localized
    players_url = get_setting('players_url', 'str')
    players_url = Dialog().input(get_localized(32313), defaultt=players_url)
    if not Dialog().yesno(
            get_localized(32032),
            get_localized(32314).format(players_url)):
        return
    set_setting('players_url', players_url, 'str')
    downloader = Downloader(
        extract_to='special://profile/addon_data/plugin.video.themoviedb.helper/players',
        download_url=players_url)
    downloader.get_extracted_zip()


def set_defaultplayer(**kwargs):
    from resources.lib.player.players import Players
    from resources.lib.addon.plugin import set_setting
    tmdb_type = kwargs.get('set_defaultplayer')
    setting_name = 'default_player_movies' if tmdb_type == 'movie' else 'default_player_episodes'
    default_player = Players(tmdb_type).select_player(detailed=True, clear_player=True)
    if not default_player:
        return
    if not default_player.get('file') or not default_player.get('mode'):
        return set_setting(setting_name, '', 'str')
    set_setting(setting_name, f'{default_player["file"]} {default_player["mode"]}', 'str')


def library_autoupdate(**kwargs):
    from xbmcgui import Dialog
    from resources.lib.update.userlist import library_autoupdate as _library_autoupdate
    from resources.lib.addon.plugin import get_localized
    if kwargs.get('force') == 'select':
        choice = Dialog().yesno(
            get_localized(32391),
            get_localized(32392),
            yeslabel=get_localized(32393),
            nolabel=get_localized(32394))
        if choice == -1:
            return
        kwargs['force'] = True if choice else False
    _library_autoupdate(
        list_slugs=kwargs.get('list_slug', None),
        user_slugs=kwargs.get('user_slug', None),
        busy_spinner=True if kwargs.get('busy_dialog', False) else False,
        force=kwargs.get('force', False))


def log_request(**kwargs):
    import xbmcvfs
    from json import dumps
    from xbmcgui import Dialog
    from resources.lib.addon.dialog import BusyDialog
    from resources.lib.api.trakt.api import TraktAPI
    from resources.lib.api.tmdb.api import TMDb
    from resources.lib.files.futils import validify_filename
    from resources.lib.files.futils import dumps_to_file
    with BusyDialog():
        kwargs['response'] = None
        if not kwargs.get('url'):
            kwargs['url'] = Dialog().input('URL')
        if not kwargs['url']:
            return
        if kwargs.get('log_request').lower() == 'trakt':
            kwargs['response'] = TraktAPI().get_response_json(kwargs['url'])
        else:
            kwargs['response'] = TMDb().get_response_json(kwargs['url'])
        if not kwargs['response']:
            Dialog().ok(kwargs['log_request'].capitalize(), f'{kwargs["url"]}\nNo Response!')
            return
        filename = validify_filename(f'{kwargs["log_request"]}_{kwargs["url"]}.json')
        dumps_to_file(kwargs, 'log_request', filename)
        msg = (
            f'[B]{kwargs["url"]}[/B]\n\n{xbmcvfs.translatePath("special://profile/addon_data/")}\n'
            f'plugin.video.themoviedb.helper/log_request\n{filename}')
        Dialog().ok(kwargs['log_request'].capitalize(), msg)
        Dialog().textviewer(filename, dumps(kwargs['response'], indent=2))


def delete_cache(delete_cache, **kwargs):
    from xbmcgui import Dialog
    from resources.lib.items.builder import ItemBuilder
    from resources.lib.api.fanarttv.api import FanartTV
    from resources.lib.api.trakt.api import TraktAPI
    from resources.lib.api.tmdb.api import TMDb
    from resources.lib.api.omdb.api import OMDb
    from resources.lib.addon.plugin import get_localized
    from resources.lib.addon.dialog import BusyDialog
    d = {
        'TMDb': lambda: TMDb(),
        'Trakt': lambda: TraktAPI(),
        'FanartTV': lambda: FanartTV(),
        'OMDb': lambda: OMDb(),
        'Item Details': lambda: ItemBuilder()}
    if delete_cache == 'select':
        m = [i for i in d]
        x = Dialog().contextmenu([get_localized(32387).format(i) for i in m])
        if x == -1:
            return
        delete_cache = m[x]
    z = d.get(delete_cache)
    if not z:
        return
    if not Dialog().yesno(get_localized(32387).format(delete_cache), get_localized(32388).format(delete_cache)):
        return
    with BusyDialog():
        z()._cache.ret_cache()._do_delete()
    Dialog().ok(get_localized(32387).format(delete_cache), get_localized(32389))


@map_kwargs({'play': 'tmdb_type'})
@get_tmdb_id
def play_external(**kwargs):
    from resources.lib.addon.logger import kodi_log
    from resources.lib.player.players import Players
    kodi_log(['lib.script.router - attempting to play\n', kwargs], 1)
    Players(**kwargs).play()


def play_using(play_using, mode='play', **kwargs):
    from resources.lib.addon.plugin import get_infolabel
    from resources.lib.files.futils import read_file
    from resources.lib.addon.parser import parse_paramstring

    def _update_from_listitem(dictionary):
        url = get_infolabel('ListItem.FileNameAndPath') or ''
        if url[-5:] == '.strm':
            url = read_file(url)
        params = {}
        if url.startswith('plugin://plugin.video.themoviedb.helper/?'):
            params = parse_paramstring(url.replace('plugin://plugin.video.themoviedb.helper/?', ''))
        if params.pop('info', None) in ['play', 'related']:
            dictionary.update(params)
        if dictionary.get('tmdb_type'):
            return dictionary
        dbtype = get_infolabel('ListItem.DBType')
        if dbtype == 'movie':
            dictionary['tmdb_type'] = 'movie'
            dictionary['tmdb_id'] = get_infolabel('ListItem.UniqueId(tmdb)')
            dictionary['imdb_id'] = get_infolabel('ListItem.UniqueId(imdb)')
            dictionary['query'] = get_infolabel('ListItem.Title')
            dictionary['year'] = get_infolabel('ListItem.Year')
            if dictionary['tmdb_id'] or dictionary['imdb_id'] or dictionary['query']:
                return dictionary
        elif dbtype == 'episode':
            dictionary['tmdb_type'] = 'tv'
            dictionary['query'] = get_infolabel('ListItem.TVShowTitle')
            dictionary['ep_year'] = get_infolabel('ListItem.Year')
            dictionary['season'] = get_infolabel('ListItem.Season')
            dictionary['episode'] = get_infolabel('ListItem.Episode')
            if dictionary['query'] and dictionary['season'] and dictionary['episode']:
                return dictionary

    if 'tmdb_type' not in kwargs and not _update_from_listitem(kwargs):
        return
    kwargs['mode'] = mode
    kwargs['player'] = play_using
    play_external(**kwargs)


def sort_list(**kwargs):
    from xbmcgui import Dialog
    from resources.lib.addon.parser import encode_url
    from resources.lib.addon.plugin import executebuiltin, format_folderpath
    from resources.lib.api.trakt.api import get_sort_methods
    sort_methods = get_sort_methods() if kwargs['info'] == 'trakt_userlist' else get_sort_methods(True)
    x = Dialog().contextmenu([i['name'] for i in sort_methods])
    if x == -1:
        return
    for k, v in sort_methods[x]['params'].items():
        kwargs[k] = v
    executebuiltin(format_folderpath(encode_url(**kwargs)))
