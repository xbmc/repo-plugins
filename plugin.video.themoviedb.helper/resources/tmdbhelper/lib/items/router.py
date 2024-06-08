from tmdbhelper.lib.addon.logger import kodi_log
from jurialmunkey.parser import parse_paramstring, reconfigure_legacy_params


class Router():
    def __init__(self, handle, paramstring):
        # plugin:// params configuration
        self.handle = handle  # plugin:// handle
        self.paramstring, *secondary_params = paramstring.split('&&')  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = reconfigure_legacy_params(**parse_paramstring(self.paramstring))  # paramstring dictionary
        if not secondary_params:
            return
        from urllib.parse import unquote_plus
        self.params['paths'] = [unquote_plus(i) for i in secondary_params]

    def play_external(self):
        from tmdbhelper.lib.player.players import Players
        from tmdbhelper.lib.api.tmdb.api import TMDb
        kodi_log(['lib.container.router - Attempting to play item\n', self.params], 1)
        if not self.params.get('tmdb_id'):
            self.params['tmdb_id'] = TMDb().get_tmdb_id(**self.params)
        Players(**self.params).play(handle=self.handle if self.handle != -1 else None)

    def context_related(self):
        from tmdbhelper.lib.script.method.context_menu import related_lists
        from tmdbhelper.lib.api.tmdb.api import TMDb
        if not self.params.get('tmdb_id'):
            self.params['tmdb_id'] = TMDb().get_tmdb_id(**self.params)
        self.params['container_update'] = True
        related_lists(include_play=True, **self.params)

    def get_directory(self, items_only=False, build_items=True):
        from tmdbhelper.lib.items.routes import get_container
        container = get_container(self.params.get('info'))(self.handle, self.paramstring, **self.params)
        container.get_tmdb_id()  # TODO: Only get this as necessary
        return container.get_directory(items_only, build_items)

    def run(self):
        if self.params.get('info') == 'play':
            return self.play_external()
        if self.params.get('info') == 'related':
            return self.context_related()
        self.get_directory()
