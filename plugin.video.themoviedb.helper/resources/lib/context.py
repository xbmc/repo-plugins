import sys
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
from resources.lib.plugin import Plugin
from resources.lib.traktapi import TraktAPI
from resources.lib.kodilibrary import KodiLibrary
import resources.lib.utils as utils
_addon = xbmcaddon.Addon('plugin.video.themoviedb.helper')
_plugin = Plugin()


def library_cleancontent_replacer(content, old, new):
    content = content.replace(old, new)
    return library_cleancontent_replacer(content, old, new) if old in content else content


def library_cleancontent(content, details='info=play'):
    content = content.replace('info=flatseasons', details)
    content = content.replace('info=details', details)
    content = content.replace('fanarttv=True', '')
    content = content.replace('widget=True', '')
    content = content.replace('localdb=True', '')
    content = content.replace('nextpage=True', '')
    content = library_cleancontent_replacer(content, '&amp;', '&')
    content = library_cleancontent_replacer(content, '&&', '&')
    content = library_cleancontent_replacer(content, '?&', '?')
    content = content + '&islocal=True' if '&islocal=True' not in content else content
    return content


def library_createpath(path):
    if xbmcvfs.exists(path):
        return path
    if xbmcvfs.mkdirs(path):
        utils.kodi_log(u'ADD LIBRARY -- Created path:\n{}'.format(path), 2)
        return path
    if _addon.getSettingBool('ignore_folderchecking'):
        utils.kodi_log(u'ADD LIBRARY -- xbmcvfs reports folder does NOT exist:\n{}\nIGNORING ERROR: User set folder checking to ignore'.format(path), 2)
        return path


def library_createfile(filename, content, *args, **kwargs):
    """
    Create the file and folder structure: filename=.strm file, content= content of file.
    *args = folders to create.
    """
    file_ext = kwargs.pop('file_ext', 'strm')
    clean_url = kwargs.pop('clean_url', True)
    path = kwargs.pop('basedir', '')
    path = path.replace('\\', '/')
    if not path:
        utils.kodi_log(u'ADD LIBRARY -- No basedir specified!', 2)
        return
    content = library_cleancontent(content) if clean_url else content
    for folder in args:
        folder = utils.validify_filename(folder)
        path = '{}{}/'.format(path, folder)
    if not content:
        utils.kodi_log(u'ADD LIBRARY -- No content specified!', 2)
        return
    if not filename:
        utils.kodi_log(u'ADD LIBRARY -- No filename specified!', 2)
        return
    if not library_createpath(path):
        xbmcgui.Dialog().ok(
            xbmc.getLocalizedString(20444),
            _addon.getLocalizedString(32122) + ' [B]{}[/B]'.format(path),
            _addon.getLocalizedString(32123))
        utils.kodi_log(u'ADD LIBRARY -- XBMCVFS unable to create path:\n{}'.format(path), 2)
        return
    filepath = '{}{}.{}'.format(path, utils.validify_filename(filename), file_ext)
    f = xbmcvfs.File(filepath, 'w')
    f.write(utils.try_encode_string(content))
    f.close()
    utils.kodi_log(u'ADD LIBRARY -- Successfully added:\n{}\n{}'.format(filepath, content), 2)
    return filepath


def library_create_nfo(tmdbtype, tmdb_id, *args, **kwargs):
    filename = 'movie' if tmdbtype == 'movie' else 'tvshow'
    content = 'https://www.themoviedb.org/{}/{}'.format(tmdbtype, tmdb_id)
    library_createfile(filename, content, file_ext='nfo', *args, **kwargs)


def library_addtvshow(basedir=None, folder=None, url=None, tmdb_id=None, tvdb_id=None, imdb_id=None, p_dialog=None):
    if not basedir or not folder or not url:
        return
    seasons = library_cleancontent_replacer(url, 'type=episode', 'type=tv')  # Clean-up flatseasons
    seasons = library_cleancontent(seasons, details='info=seasons')
    seasons = KodiLibrary().get_directory(seasons)
    library_create_nfo('tv', tmdb_id, folder, basedir=basedir)
    s_count = 0
    s_total = len(seasons)
    for season in seasons:
        s_count += 1
        if not season.get('season'):
            continue  # Skip special seasons S00
        season_name = '{} {}'.format(xbmc.getLocalizedString(20373), season.get('season'))
        p_dialog.update((s_count * 100) // s_total, message=u'Adding {} - {} to library...'.format(season.get('showtitle'), season_name)) if p_dialog else None
        episodes = library_cleancontent_replacer(season.get('file'), 'type=episode', 'type=season')  # Clean to prevent flatseasons
        episodes = library_cleancontent(episodes, details='info=episodes')
        episodes = KodiLibrary().get_directory(episodes)
        i_count = 0
        i_total = len(episodes)
        for episode in episodes:
            i_count += 1
            if not episode.get('episode'):
                continue  # Skip special episodes E00
            s_num = episode.get('season')
            e_num = episode.get('episode')
            episode_name = 'S{:02d}E{:02d} - {}'.format(
                utils.try_parse_int(s_num),
                utils.try_parse_int(e_num),
                utils.validify_filename(episode.get('title')))
            if _plugin.get_db_info(info='dbid', tmdbtype='episode', imdb_id=imdb_id, tmdb_id=tmdb_id, season=s_num, episode=e_num):
                utils.kodi_log(u'Trakt List Add to Library\nFound {} - {} in library. Skipping...'.format(episode.get('showtitle'), episode_name))
                p_dialog.update((i_count * 100) // i_total, message=u'Found {} in library. Skipping...'.format(episode_name)) if p_dialog else None
                continue  # Skip added items
            p_dialog.update((i_count * 100) // i_total, message=u'Adding {} to library...'.format(episode_name)) if p_dialog else None
            episode_path = library_cleancontent(episode.get('file'))
            library_createfile(episode_name, episode_path, folder, season_name, basedir=basedir)


def browse():
    tmdb_id = sys.listitem.getProperty('tvshow.tmdb_id')
    path = 'plugin://plugin.video.themoviedb.helper/'
    path = path + '?info=seasons&type=tv&nextpage=True&tmdb_id={}'.format(tmdb_id)
    path = path + '&fanarttv=True' if _addon.getSettingBool('fanarttv_lookup') else path
    command = 'Container.Update({})' if xbmc.getCondVisibility("Window.IsMedia") else 'ActivateWindow(videos,{},return)'
    xbmc.executebuiltin(command.format(path))


def play():
    with utils.busy_dialog():
        tmdb_id, season, episode = None, None, None
        dbtype = sys.listitem.getVideoInfoTag().getMediaType()

        if dbtype == 'episode':
            tmdb_id = sys.listitem.getProperty('tvshow.tmdb_id')
            season = sys.listitem.getVideoInfoTag().getSeason()
            episode = sys.listitem.getVideoInfoTag().getEpisode()
            xbmc.executebuiltin('RunScript(plugin.video.themoviedb.helper,play={},tmdb_id={},season={},episode={},force_dialog=True)'.format(
                dbtype, tmdb_id, season, episode))

        elif dbtype == 'movie':
            tmdb_id = sys.listitem.getProperty('tmdb_id')
            xbmc.executebuiltin('RunScript(plugin.video.themoviedb.helper,play={},tmdb_id={},force_dialog=True)'.format(
                dbtype, tmdb_id))


def library_userlist(user_slug=None, list_slug=None, confirmation_dialog=True, allow_update=True):
    user_slug = user_slug or sys.listitem.getProperty('Item.user_slug')
    list_slug = list_slug or sys.listitem.getProperty('Item.list_slug')

    with utils.busy_dialog():
        request = TraktAPI().get_response_json('users', user_slug, 'lists', list_slug, 'items')
        if not request:
            return

    i_count = 0
    i_total = len(request)

    if confirmation_dialog:
        d_head = _addon.getLocalizedString(32125)
        d_body = _addon.getLocalizedString(32126)
        d_body += '\n[B]{}[/B] {} [B]{}[/B]'.format(list_slug, _addon.getLocalizedString(32127), user_slug)
        d_body += '\n\n[B][COLOR=red]{}[/COLOR][/B] '.format(xbmc.getLocalizedString(14117)) if i_total > 20 else '\n\n'
        d_body += '{} [B]{}[/B] {}.'.format(_addon.getLocalizedString(32128), i_total, _addon.getLocalizedString(32129))
        if not xbmcgui.Dialog().yesno(d_head, d_body):
            return

    p_dialog = xbmcgui.DialogProgressBG()
    p_dialog.create('TMDbHelper', 'Adding items to library...')
    basedir_movie = _addon.getSettingString('movies_library') or 'special://profile/addon_data/plugin.video.themoviedb.helper/movies/'
    basedir_tv = _addon.getSettingString('tvshows_library') or 'special://profile/addon_data/plugin.video.themoviedb.helper/tvshows/'
    all_movies = []
    all_tvshows = []

    for i in request:
        i_count += 1
        i_type = i.get('type')
        if i_type not in ['movie', 'show']:
            continue  # Only get movies or tvshows

        item = i.get(i_type, {})
        tmdb_id = item.get('ids', {}).get('tmdb')
        imdb_id = item.get('ids', {}).get('imdb')
        tvdb_id = item.get('ids', {}).get('tvdb')
        if not tmdb_id:
            continue  # Don't bother if there isn't a tmdb_id as lookup is too expensive for long lists

        if i_type == 'movie':  # Add any movies
            # all_movies.append(('title', item.get('title')))
            content = 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_id={}&type=movie'.format(tmdb_id)
            folder = u'{} ({})'.format(item.get('title'), item.get('year'))
            movie_name = u'{} ({})'.format(item.get('title'), item.get('year'))
            db_file = _plugin.get_db_info(info='file', tmdbtype='movie', imdb_id=imdb_id, tmdb_id=tmdb_id)
            if db_file:
                all_movies.append(('filename', db_file.replace('\\', '/').split('/')[-1]))
                p_dialog.update((i_count * 100) // i_total, message=u'Found {} in library. Skipping...'.format(movie_name))
                utils.kodi_log(u'Trakt List Add to Library\nFound {} in library. Skipping...'.format(movie_name), 0)
                continue
            p_dialog.update((i_count * 100) // i_total, message=u'Adding {} to library...'.format(movie_name))
            utils.kodi_log(u'Adding {} to library...'.format(movie_name), 0)
            db_file = library_createfile(movie_name, content, folder, basedir=basedir_movie)
            library_create_nfo('movie', tmdb_id, folder, basedir=basedir_movie)
            all_movies.append(('filename', db_file.split('/')[-1]))

        if i_type == 'show':  # Add whole tvshows
            all_tvshows.append(('title', item.get('title')))
            content = 'plugin://plugin.video.themoviedb.helper/?info=seasons&nextpage=True&tmdb_id={}&type=tv'.format(tmdb_id)
            folder = u'{}'.format(item.get('title'))
            p_dialog.update((i_count * 100) // i_total, message=u'Adding {} to library...'.format(item.get('title')))
            library_addtvshow(basedir=basedir_tv, folder=folder, url=content, tmdb_id=tmdb_id, imdb_id=imdb_id, tvdb_id=tvdb_id, p_dialog=p_dialog)

    p_dialog.close()
    create_playlist(all_movies, 'movies', user_slug, list_slug) if all_movies else None
    create_playlist(all_tvshows, 'tvshows', user_slug, list_slug) if all_tvshows else None
    if allow_update and _addon.getSettingBool('auto_update'):
        xbmc.executebuiltin('UpdateLibrary(video)')


def create_playlist(items, dbtype, user_slug, list_slug):
    """
    Creates a smart playlist from a list of titles
    """
    filename = '{}-{}-{}'.format(user_slug, list_slug, dbtype)
    filepath = 'special://profile/playlists/video/'
    fcontent = u'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    fcontent += u'\n<smartplaylist type="{}">'.format(dbtype)
    fcontent += u'\n    <name>{} by {} ({})</name>'.format(list_slug, user_slug, dbtype)
    fcontent += u'\n    <match>any</match>'
    for i in items:
        fcontent += u'\n    <rule field="{}" operator="is"><value>{}</value></rule>'.format(i[0], i[1])
    fcontent += u'\n</smartplaylist>'
    library_createfile(filename, fcontent, basedir=filepath, file_ext='xsp', clean_url=False)


def library():
    with utils.busy_dialog():
        title = utils.validify_filename(sys.listitem.getVideoInfoTag().getTitle())
        dbtype = sys.listitem.getVideoInfoTag().getMediaType()
        basedir_movie = _addon.getSettingString('movies_library') or 'special://profile/addon_data/plugin.video.themoviedb.helper/movies/'
        basedir_tv = _addon.getSettingString('tvshows_library') or 'special://profile/addon_data/plugin.video.themoviedb.helper/tvshows/'
        auto_update = _addon.getSettingBool('auto_update') or False

        # Setup our folders and file names
        if dbtype == 'movie':
            folder = '{} ({})'.format(title, sys.listitem.getVideoInfoTag().getYear())
            movie_name = '{} ({})'.format(title, sys.listitem.getVideoInfoTag().getYear())
            library_createfile(movie_name, sys.listitem.getPath(), folder, basedir=basedir_movie)
            library_create_nfo('movie', sys.listitem.getProperty('tmdb_id'), folder, basedir=basedir_movie)
            xbmc.executebuiltin('UpdateLibrary(video, {})'.format(basedir_movie)) if auto_update else None

        elif dbtype == 'episode':
            folder = sys.listitem.getVideoInfoTag().getTVShowTitle()
            season_name = 'Season {}'.format(sys.listitem.getVideoInfoTag().getSeason())
            episode_name = 'S{:02d}E{:02d} - {}'.format(
                utils.try_parse_int(sys.listitem.getVideoInfoTag().getSeason()),
                utils.try_parse_int(sys.listitem.getVideoInfoTag().getEpisode()),
                title)
            library_createfile(episode_name, sys.listitem.getPath(), folder, season_name, basedir=basedir_tv)
            library_create_nfo('tv', sys.listitem.getProperty('tvshow.tmdb_id'), folder, basedir=basedir_tv)
            xbmc.executebuiltin('UpdateLibrary(video, {})'.format(basedir_tv)) if auto_update else None

        elif dbtype == 'tvshow':
            folder = sys.listitem.getVideoInfoTag().getTVShowTitle() or title
            library_addtvshow(
                basedir=basedir_tv, folder=folder, url=sys.listitem.getPath(),
                tmdb_id=sys.listitem.getProperty('tmdb_id'))
            xbmc.executebuiltin('UpdateLibrary(video, {})'.format(basedir_tv)) if auto_update else None

        elif dbtype == 'season':
            folder = sys.listitem.getVideoInfoTag().getTVShowTitle()
            episodes = KodiLibrary().get_directory(sys.listitem.getPath())
            season_name = 'Season {}'.format(sys.listitem.getVideoInfoTag().getSeason())
            for episode in episodes:
                if not episode.get('episode'):
                    continue  # Skip special episodes E00
                episode_path = library_cleancontent(episode.get('file'))
                episode_name = 'S{:02d}E{:02d} - {}'.format(
                    utils.try_parse_int(episode.get('season')),
                    utils.try_parse_int(episode.get('episode')),
                    utils.validify_filename(episode.get('title')))
                library_createfile(episode_name, episode_path, folder, season_name, basedir=basedir_tv)
            library_create_nfo('tv', sys.listitem.getProperty('tvshow.tmdb_id'), folder, basedir=basedir_tv)
            xbmc.executebuiltin('UpdateLibrary(video, {})'.format(basedir_tv)) if auto_update else None

        else:
            return


def sync_userlist(remove_item=False):
    dbtype = sys.listitem.getVideoInfoTag().getMediaType()
    user_list = sys.listitem.getProperty('container.list_slug') if remove_item else None
    tmdb_id = sys.listitem.getProperty('tvshow.tmdb_id')
    imdb_id = sys.listitem.getUniqueID('imdb')
    tvdb_id = None
    if not dbtype == 'episode':
        tmdb_id = sys.listitem.getProperty('tmdb_id') or sys.listitem.getUniqueID('tmdb')
        tvdb_id = sys.listitem.getUniqueID('tvdb')
    if dbtype == 'movie':
        item_type = 'movie'
    elif dbtype in ['tvshow', 'season', 'episode']:
        item_type = 'show'
    else:  # Not the right type of item so lets exit
        return
    TraktAPI().sync_userlist(item_type, tmdb_id=tmdb_id, tvdb_id=tvdb_id, imdb_id=imdb_id, remove_item=remove_item, user_list=user_list)
    xbmc.executebuiltin('Container.Refresh')


def refresh_item():
    dbtype = sys.listitem.getVideoInfoTag().getMediaType()
    if dbtype == 'episode':
        d_args = (
            'tv', sys.listitem.getProperty('tvshow.tmdb_id'),
            sys.listitem.getVideoInfoTag().getSeason(),
            sys.listitem.getVideoInfoTag().getEpisode())
    elif dbtype == 'tvshow':
        d_args = ('tv', sys.listitem.getProperty('tmdb_id'))
    elif dbtype == 'movie':
        d_args = ('movie', sys.listitem.getProperty('tmdb_id'))
    else:
        return
    details = _plugin.tmdb.get_detailed_item(*d_args, cache_refresh=True)
    if details:
        xbmcgui.Dialog().ok(_addon.getLocalizedString(32144), _addon.getLocalizedString(32143).format(details.get('label')))
    xbmc.executebuiltin('Container.Refresh')


def action(action, tmdb_id=None, tmdb_type=None, season=None, episode=None, label=None):
    _traktapi = TraktAPI()

    if action == 'history':
        func = _traktapi.sync_history
    elif action == 'collection':
        func = _traktapi.sync_collection
    elif action == 'watchlist':
        func = _traktapi.sync_watchlist
    elif action == 'add_to_userlist':
        return sync_userlist()
    elif action == 'remove_from_userlist':
        return sync_userlist(remove_item=True)
    elif action == 'library_userlist':
        return library_userlist()
    elif action == 'library':
        return library()
    elif action == 'refresh_item':
        return refresh_item()
    elif action == 'play':
        return play()
    elif action == 'open':
        return browse()
    else:
        return

    with utils.busy_dialog():
        if tmdb_id and tmdb_type:  # Passed details via script
            dbtype = utils.type_convert(tmdb_type, 'dbtype')
            label = label or 'this {}'.format(utils.type_convert(tmdb_type, 'trakt'))
            parent_tmdb_id = tmdb_id
        else:  # Context menu so retrieve details from listitem
            label = sys.listitem.getLabel()
            dbtype = sys.listitem.getVideoInfoTag().getMediaType()
            tmdb_id = sys.listitem.getProperty('tmdb_id')
            parent_tmdb_id = sys.listitem.getProperty('tvshow.tmdb_id') if dbtype == 'episode' else tmdb_id
            season = sys.listitem.getVideoInfoTag().getSeason() if dbtype == 'episode' else None
            episode = sys.listitem.getVideoInfoTag().getEpisode() if dbtype == 'episode' else None

        if tmdb_type == 'episode':  # Passed episode details via script
            if not season or not episode:  # Need season and episode for episodes
                return  # Need season and episode if run from script so leave
            # Retrieve episode details so that we can get tmdb_id for episode
            episode_details = _plugin.tmdb.get_detailed_item(tmdb_type, parent_tmdb_id, season=season, episode=episode)
            tmdb_id = episode_details.get('infoproperties', {}).get('imdb_id')

        if dbtype == 'movie':
            tmdb_type = 'movie'
        elif dbtype == 'tvshow':
            tmdb_type = 'tv'
        elif dbtype == 'episode':
            tmdb_type = 'episode'
        else:
            return

        # Check if we're adding or removing the item and confirm with the user that they want to do that
        trakt_ids = func(utils.type_convert(tmdb_type, 'trakt'), 'tmdb', cache_refresh=True)
        boolean = 'remove' if int(tmdb_id) in trakt_ids else 'add'
        dialog_header = 'Trakt {0}'.format(action.capitalize())
        dialog_text = xbmcaddon.Addon().getLocalizedString(32065) if boolean == 'add' else xbmcaddon.Addon().getLocalizedString(32064)
        dialog_text = dialog_text.format(utils.try_decode_string(label), action.capitalize(), tmdb_type, tmdb_id)
        dialog_text = dialog_text + ' Season: {}  Episode: {}'.format(season, episode) if dbtype == 'episode' else dialog_text
        if not xbmcgui.Dialog().yesno(dialog_header, dialog_text):
            return

        with utils.busy_dialog():
            slug_type = 'show' if tmdb_type == 'episode' else utils.type_convert(tmdb_type, 'trakt')
            trakt_type = utils.type_convert(tmdb_type, 'trakt')
            slug = _traktapi.get_traktslug(slug_type, 'tmdb', parent_tmdb_id)
            item = _traktapi.get_details(slug_type, slug, season=season, episode=episode)
            items = {trakt_type + 's': [item]}
            func(slug_type, mode=boolean, items=items)

        dialog_header = 'Trakt {0}'.format(action.capitalize())
        dialog_text = xbmcaddon.Addon().getLocalizedString(32062) if boolean == 'add' else xbmcaddon.Addon().getLocalizedString(32063)
        dialog_text = dialog_text.format(tmdb_id, action.capitalize())
        xbmcgui.Dialog().ok(dialog_header, dialog_text)
        xbmc.executebuiltin('Container.Refresh')
