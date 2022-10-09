from resources.lib.addon.logger import kodi_log
from resources.lib.addon.parser import parse_paramstring, reconfigure_legacy_params

""" Lazyimports
from resources.lib.player.players import Players
from resources.lib.api.tmdb.api import TMDb
from resources.lib.script.method import related_lists
from resources.lib.items.routes import get_container
"""


class Router():
    def __init__(self, handle, paramstring):
        # plugin:// params configuration
        self.handle = handle  # plugin:// handle
        self.paramstring = paramstring  # plugin://plugin.video.themoviedb.helper?paramstring
        self.params = reconfigure_legacy_params(**parse_paramstring(self.paramstring))  # paramstring dictionary

    def play_external(self):
        from resources.lib.player.players import Players
        from resources.lib.api.tmdb.api import TMDb
        kodi_log(['lib.container.router - Attempting to play item\n', self.params], 1)
        if not self.params.get('tmdb_id'):
            self.params['tmdb_id'] = TMDb().get_tmdb_id(**self.params)
        Players(**self.params).play(handle=self.handle if self.handle != -1 else None)

    def context_related(self):
        from resources.lib.script.method import related_lists
        from resources.lib.api.tmdb.api import TMDb
        if not self.params.get('tmdb_id'):
            self.params['tmdb_id'] = TMDb().get_tmdb_id(**self.params)
        self.params['container_update'] = True
        related_lists(include_play=True, **self.params)

    def get_directory(self):
        from resources.lib.items.routes import get_container
        container = get_container(self.params.get('info'))(self.handle, self.paramstring, **self.params)
        container.get_tmdb_id()  # TODO: Only get this as necessary
        container.get_directory()

    def run(self):
        if self.params.get('info') == 'play':
            return self.play_external()
        if self.params.get('info') == 'related':
            return self.context_related()
        self.get_directory()
