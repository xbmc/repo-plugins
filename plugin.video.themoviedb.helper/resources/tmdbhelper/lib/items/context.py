# Module: default
# Author: jurialmunkey
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from tmdbhelper.lib.addon.plugin import get_setting


CONTEXT_MENU_ITEMS = {
    # Browse Lists
    '$ADDON[plugin.video.themoviedb.helper 32235]': {
        'command': 'RunScript(plugin.video.themoviedb.helper,related_lists,{})',
        'setting': 'contextmenu_related_lists',
        'episode': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}', 'episode': '{episode}'},
        'other': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    },
    # Trakt Options
    '$ADDON[plugin.video.themoviedb.helper 32295]': {
        'command': 'RunScript(plugin.video.themoviedb.helper,sync_trakt,{})',
        'setting': 'contextmenu_sync_trakt',
        'episode': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}', 'season': '{season}', 'episode': '{episode}'},
        'other': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    },
    # Manage Artwork
    '$ADDON[plugin.video.themoviedb.helper 32222]': {
        'command': 'RunScript(plugin.video.themoviedb.helper,manage_artwork,{})',
        'setting': 'contextmenu_manage_artwork',
        'movie': {'tmdb_type': 'movie', 'tmdb_id': '{tmdb_id}'},
        'tvshow': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}'},
        'season': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}'},
        'episode': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}'}
    },
    # Refresh Details
    '$ADDON[plugin.video.themoviedb.helper 32233]': {
        'command': 'RunScript(plugin.video.themoviedb.helper,refresh_details,{})',
        'setting': 'contextmenu_refresh_details',
        'episode': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}', 'episode': '{episode}'},
        'season': {'tmdb_type': 'tv', 'tmdb_id': '{tmdb_id}', 'season': '{season}'},
        'other': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    },
    # Add to Library
    '$LOCALIZE[20444]': {
        'command': 'RunScript(plugin.video.themoviedb.helper,add_to_library,{})',
        'setting': 'contextmenu_add_to_library',
        'movie': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'},
        'tvshow': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'},
        'season': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'},
        'episode': {'tmdb_type': '{tmdb_type}', 'tmdb_id': '{tmdb_id}'}
    }

}


class ContextMenu():
    """ Builds a context menu for a listitem based upon a definition of formattable keys
    If context params have format key in self.info but it is empty then item isn't built
    Context menu builds only for specified mediatypes (use other for all others)
    """

    def __init__(self, listitem):
        self._li = listitem
        self.info = {
            'ftv_id': self._li.ftv_id,
            'tmdb_id': self._li.tmdb_id,
            'tmdb_type': self._li.tmdb_type,
            'trakt_type': self._li.trakt_type,
            'season': self._li.season,
            'episode': self._li.episode,
        }
        self.mediatype = self._li.infolabels.get('mediatype')

    def get(self, context=None):
        context = context or CONTEXT_MENU_ITEMS
        return [(name, str(item)) for name, item in (
            (name, self._build_item(mediatypes)) for name, mediatypes in context.items()) if item]

    def _build_item(self, mediatypes):
        params_def = mediatypes.get(self.mediatype, mediatypes.get('other'))
        router_def = mediatypes.get('command')
        if not params_def or not router_def:
            return

        if not get_setting(mediatypes['setting']):
            return

        item = {}
        for k, v in params_def.items():
            try:  # Need to try accept in case hard-coded int/bool etc.
                value = v.format(**self.info)
            except AttributeError:
                value = v
            if value in ['None', '', None]:
                return  # Don't create a context item if we don't have a formatter value
            item[k] = value

        router_str = ','.join([f'{k}={v}' for k, v in item.items()])
        return router_def.format(router_str)
