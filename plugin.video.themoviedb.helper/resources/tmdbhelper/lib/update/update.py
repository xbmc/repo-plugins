import xbmcvfs
from xbmcgui import Dialog
from tmdbhelper.lib.addon.dialog import BusyDialog
from tmdbhelper.lib.addon.plugin import get_setting, get_localized
from jurialmunkey.parser import try_int
from tmdbhelper.lib.files.futils import validify_filename, make_path, write_to_file, get_tmdb_id_nfo
from tmdbhelper.lib.api.trakt.api import TraktAPI
from tmdbhelper.lib.addon.logger import kodi_log


STRM_MOVIE = 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_id={}&tmdb_type=movie&islocal=True'
STRM_EPISODE = 'plugin://plugin.video.themoviedb.helper/?info=play&tmdb_type=tv&islocal=True&tmdb_id={}&season={}&episode={}'
BASEDIR_MOVIE = get_setting('movies_library', 'str') or 'special://profile/addon_data/plugin.video.themoviedb.helper/movies/'
BASEDIR_TV = get_setting('tvshows_library', 'str') or 'special://profile/addon_data/plugin.video.themoviedb.helper/tvshows/'
NFOFILE_MOVIE = u'movie-tmdbhelper' if get_setting('alternative_nfo') else u'movie'
NFOFILE_TV = u'tvshow-tmdbhelper' if get_setting('alternative_nfo') else u'tvshow'
"""
IMPORTANT: These limits are set to prevent excessive API data usage.
Please respect the APIs that provide this data for free.
"""
LIBRARY_ADD_LIMIT_TVSHOWS = 500
LIBRARY_ADD_LIMIT_MOVIES = 2500


def replace_content(content, old, new):
    content = content.replace(old, new)
    return replace_content(content, old, new) if old in content else content


def clean_content(content, details='info=play'):
    content = content.replace('info=related', details)
    content = content.replace('info=flatseasons', details)
    content = content.replace('info=details', details)
    content = content.replace('fanarttv=True', '')
    content = content.replace('widget=True', '')
    content = content.replace('localdb=True', '')
    content = content.replace('nextpage=True', '')
    content = replace_content(content, '&amp;', '&')
    content = replace_content(content, '&&', '&')
    content = replace_content(content, '?&', '?')
    content = content + '&islocal=True' if '&islocal=True' not in content else content
    return content


def check_overlimit(request):
    """
    IMPORTANT: Do not change limits.
    Please respect the APIs that provide this data for free.
    Returns None if NOT overlimit. Otherwise returns dict containing totals in request.
    """
    if len(request) <= min(LIBRARY_ADD_LIMIT_TVSHOWS, LIBRARY_ADD_LIMIT_MOVIES):
        return

    totals = {}
    for i in request:
        totals[i.get('type', 'none')] = totals.get(i.get('type', 'none'), 0) + 1

    if totals.get('show', 0) <= LIBRARY_ADD_LIMIT_TVSHOWS:
        if totals.get('movie', 0) <= LIBRARY_ADD_LIMIT_MOVIES:
            return

    return totals


def create_file(content, filename, *args, **kwargs):
    """
    Create the file and folder structure: filename=.strm file, content= content of file.
    *args = folders to create.
    """

    # Validify and build path
    path = kwargs.get('basedir', '').replace('\\', '/')  # Convert MS-DOS style paths to UNIX style
    if not path:  # Make sure we actually have a basedir
        return
    for folder in args:
        folder = validify_filename(folder)
        path = f'{path}{folder}/'

    # Validify content of file
    if kwargs.get('clean_url', True):
        content = clean_content(content)
    if not content:
        return
    if not filename:
        return

    # Check that we can actually make the path
    if not make_path(path, warn_dialog=True):
        return

    # Write out our file
    filename = f'{validify_filename(filename)}.{kwargs.get("file_ext", "strm")}'
    filepath = f'{path}{filename}'
    write_to_file(content, path, filename, join_addon_data=False)
    kodi_log(['ADD LIBRARY -- Successfully added:\n', filepath, '\n', content], 2)
    return filepath


def create_nfo(tmdb_type, tmdb_id, *args, **kwargs):
    filename = NFOFILE_MOVIE if tmdb_type == 'movie' else NFOFILE_TV
    content = f'https://www.themoviedb.org/{tmdb_type}/{tmdb_id}'
    kwargs['file_ext'], kwargs['clean_url'] = 'nfo', False
    create_file(content, filename, *args, **kwargs)


def create_playlist(dbtype, user_slug, list_slug):
    """ Creates a smart playlist from a list of titles """
    filename = f'{user_slug}-{list_slug}-{dbtype}'
    filepath = u'special://profile/playlists/video/'
    fcontent = [u'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>']
    fcontent.append(f'<smartplaylist type="{dbtype}">')
    fcontent.append(f'    <name>{list_slug} by {user_slug} ({dbtype})</name>')
    fcontent.append(u'    <match>all</match>')
    fcontent.append(f'    <rule field="tag" operator="is"><value>Trakt User {user_slug}</value></rule>')
    fcontent.append(f'    <rule field="tag" operator="is"><value>Trakt List {list_slug}</value></rule>')
    fcontent.append(u'</smartplaylist>')
    create_file(u'\n'.join(fcontent), filename, basedir=filepath, file_ext='xsp', clean_url=False)


def get_unique_folder(name, tmdb_id, basedir):
    nfo_id = get_tmdb_id_nfo(basedir, name) if name in xbmcvfs.listdir(basedir)[0] else None
    if nfo_id and try_int(nfo_id) != try_int(tmdb_id):
        name += f' (TMDB {tmdb_id})'
    return name


def get_userlist(user_slug=None, list_slug=None, confirm=True, busy_spinner=True):
    with BusyDialog(is_enabled=busy_spinner):
        if list_slug.startswith('watchlist'):
            path = ['users', user_slug, list_slug]
        else:
            path = ['users', user_slug, 'lists', list_slug, 'items']
        request = TraktAPI().get_response_json(*path)
    if not request:
        return
    if confirm:
        d_head = get_localized(32125)
        i_check_limits = check_overlimit(request)
        if i_check_limits:
            # List over limit so inform user that it is too large to add
            d_body = [
                get_localized(32168).format(list_slug, user_slug),
                get_localized(32170).format(i_check_limits.get('show'), i_check_limits.get('movie')),
                '',
                get_localized(32164).format(LIBRARY_ADD_LIMIT_TVSHOWS, LIBRARY_ADD_LIMIT_MOVIES)]
            Dialog().ok(d_head, '\n'.join(d_body))
            return
        elif isinstance(confirm, bool) or len(request) > confirm:
            # List is within limits so ask for confirmation before adding it
            d_body = [
                get_localized(32168).format(list_slug, user_slug),
                get_localized(32171).format(len(request)) if len(request) > 20 else '',
                '',
                get_localized(32126)]
            if not Dialog().yesno(d_head, '\n'.join(d_body)):
                return
    return request
