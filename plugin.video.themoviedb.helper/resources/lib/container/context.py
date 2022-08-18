from json import dumps
from resources.lib.addon.constants import CONTEXT_MENU_ITEMS


class ContextMenu():
    """ Builds a context menu for a listitem based upon a definition of formattable keys
    If context params have format key in self.info but it is empty then item isn't built
    Context menu builds only for specified mediatypes (use other for all others)
    """

    def __init__(self, listitem):
        self._li = listitem
        self.info = {
            'ftv_id': self._li.get_ftv_id(),
            'tmdb_id': self._li.get_tmdb_id(),
            'tmdb_type': self._li.get_tmdb_type(),
            'trakt_type': self._li.get_trakt_type(),
            'season': self._li.infolabels.get('season'),
            'episode': self._li.infolabels.get('episode'),
        }
        self.mediatype = self._li.infolabels.get('mediatype')

    def get(self, context=None):
        context = context or CONTEXT_MENU_ITEMS
        return [(name, dumps(item)) for name, item in (
            (name, self._build_item(mediatypes)) for name, mediatypes in context.items()) if item]

    def _build_item(self, mediatypes):
        params_def = mediatypes.get(self.mediatype, mediatypes.get('other'))
        if not params_def:
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
        return item
