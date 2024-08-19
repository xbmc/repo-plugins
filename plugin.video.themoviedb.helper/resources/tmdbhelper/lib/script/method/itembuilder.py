# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from tmdbhelper.lib.script.method.decorators import is_in_kwargs, get_tmdb_id


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def manage_artwork(tmdb_id=None, tmdb_type=None, season=None, **kwargs):
    from tmdbhelper.lib.items.builder import ItemBuilder
    ItemBuilder().manage_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def select_artwork(tmdb_id=None, tmdb_type=None, season=None, **kwargs):
    from tmdbhelper.lib.items.builder import ItemBuilder
    ItemBuilder().select_artwork(tmdb_id=tmdb_id, tmdb_type=tmdb_type, season=season)


@is_in_kwargs({'tmdb_type': True})
@get_tmdb_id
def refresh_details(tmdb_id=None, tmdb_type=None, season=None, episode=None, confirm=True, **kwargs):
    from xbmcgui import Dialog
    from tmdbhelper.lib.items.builder import ItemBuilder
    from tmdbhelper.lib.addon.dialog import BusyDialog
    from tmdbhelper.lib.addon.plugin import get_localized
    from tmdbhelper.lib.script.method.kodi_utils import container_refresh
    with BusyDialog():
        details = ItemBuilder().get_item(tmdb_type, tmdb_id, season, episode, cache_refresh=True) or {}
        details = details.get('listitem')
    if details and confirm:
        Dialog().ok('TMDbHelper', get_localized(32234).format(tmdb_type, tmdb_id))
        container_refresh()
    return details
