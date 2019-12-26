import sys
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.traktapi import traktAPI
import resources.lib.utils as utils


def action(action):
    _traktapi = traktAPI()

    if action == 'history':
        func = _traktapi.sync_history
    elif action == 'collection':
        func = _traktapi.sync_collection
    elif action == 'watchlist':
        func = _traktapi.sync_watchlist
    else:
        return

    with utils.busy_dialog():
        label = sys.listitem.getLabel()
        dbtype = sys.listitem.getVideoInfoTag().getMediaType()
        tmdb_id = sys.listitem.getProperty('tmdb_id')
        tmdb_type = 'movie' if dbtype == 'movie' else 'tv'
        trakt_ids = func(utils.type_convert(tmdb_type, 'trakt'), 'tmdb')
        boolean = 'remove' if int(tmdb_id) in trakt_ids else 'add'

    dialog_header = 'Trakt {0}'.format(action.capitalize())
    dialog_text = xbmcaddon.Addon().getLocalizedString(32065) if boolean == 'add' else xbmcaddon.Addon().getLocalizedString(32064)
    dialog_text = dialog_text.format(label, action.capitalize(), dbtype.capitalize(), tmdb_id)
    if not xbmcgui.Dialog().yesno(dialog_header, dialog_text):
        return

    with utils.busy_dialog():
        trakt_type = utils.type_convert(dbtype, 'trakt')
        slug_type = 'show' if dbtype == 'episode' else trakt_type
        slug = _traktapi.get_traktslug(slug_type, 'tmdb', tmdb_id)
        season = sys.listitem.getVideoInfoTag().getSeason() if dbtype == 'episode' else None
        episode = sys.listitem.getVideoInfoTag().getEpisode() if dbtype == 'episode' else None
        item = _traktapi.get_details(slug_type, slug, season=season, episode=episode)
        items = {trakt_type + 's': [item]}
        func(slug_type, mode=boolean, items=items)

    dialog_header = 'Trakt {0}'.format(action.capitalize())
    dialog_text = xbmcaddon.Addon().getLocalizedString(32062) if boolean == 'add' else xbmcaddon.Addon().getLocalizedString(32063)
    dialog_text = dialog_text.format(tmdb_id, action.capitalize())
    xbmcgui.Dialog().ok(dialog_header, dialog_text)
    xbmc.executebuiltin('Container.Refresh')
