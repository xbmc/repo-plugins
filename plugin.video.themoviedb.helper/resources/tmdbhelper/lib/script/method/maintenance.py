# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


def clean_old_databases():
    """ Once-off routine to delete old unused database versions to avoid wasting disk space """
    from tmdbhelper.lib.files.futils import delete_folder
    from tmdbhelper.lib.addon.plugin import get_setting
    for f in ['database', 'database_v2', 'database_v3', 'database_v4', 'database_v5']:
        delete_folder(f, force=True, check_exists=True)
    save_path = get_setting('image_location', 'str')
    for f in ['blur', 'crop', 'desaturate', 'colors']:
        delete_folder(f, force=True, check_exists=True)
        if not save_path:
            continue
        delete_folder(f'{save_path}{f}/', force=True, check_exists=True, join_addon_data=False)


def recache_kodidb(notification=True):
    from tmdbhelper.lib.addon.plugin import ADDONPATH
    from tmdbhelper.lib.api.kodi.rpc import KodiLibrary
    from tmdbhelper.lib.addon.logger import TimerFunc
    from xbmcgui import Dialog
    with TimerFunc('KodiLibrary sync took', inline=True):
        KodiLibrary('movie', cache_refresh=True)
        KodiLibrary('tvshow', cache_refresh=True)
    if not notification:
        return
    Dialog().notification('TMDbHelper', 'Kodi Library cached to memory', icon=f'{ADDONPATH}/icon.png')


def delete_cache(delete_cache, **kwargs):
    from xbmcgui import Dialog
    from tmdbhelper.lib.items.builder import ItemBuilder
    from tmdbhelper.lib.api.fanarttv.api import FanartTV
    from tmdbhelper.lib.api.trakt.api import TraktAPI
    from tmdbhelper.lib.api.tmdb.api import TMDb
    from tmdbhelper.lib.api.omdb.api import OMDb
    from tmdbhelper.lib.addon.plugin import get_localized
    from tmdbhelper.lib.addon.dialog import BusyDialog
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
