from tmdbhelper.lib.update.update import get_userlist
from tmdbhelper.lib.addon.plugin import executebuiltin


class LibraryCommonFunctions():
    busy_spinner = False

    def _start(self):
        if self.p_dialog:
            self.p_dialog.create(self._msg_title, self._msg_start)

    def _finish(self, update=True):
        if self.p_dialog:
            self.p_dialog.close()
        if self.debug_logging:
            self._log._clean()  # Clean up old log files first
            self._log._out()
        if self.clean_library:
            executebuiltin('CleanLibrary(video)')
        if self.auto_update and update:
            executebuiltin('UpdateLibrary(video)')

    def _update(self, count, total, **kwargs):
        if self.p_dialog:
            self.p_dialog.update((((count + 1) * 100) // total), **kwargs)

    def add_userlist(self, user_slug=None, list_slug=None, confirm=True, force=False, **kwargs):
        request = get_userlist(user_slug=user_slug, list_slug=list_slug, confirm=confirm, busy_spinner=self.busy_spinner)
        if not request:
            return
        i_total = len(request)

        for x, i in enumerate(request):
            self._update(x, i_total, message=f'Updating {i.get(i.get("type"), {}).get("title")}...')
            self._add_userlist_item(i, force=force, user_slug=user_slug, list_slug=list_slug)

    def _add_userlist_item(self, i, force=False, user_slug=None, list_slug=None):
        i_type = i.get('type')
        if i_type == 'movie':
            func = self.add_movie
        elif i_type == 'show':
            func = self.add_tvshow
        else:
            return

        item = i.get(i_type, {})
        tmdb_id = item.get('ids', {}).get('tmdb')
        imdb_id = item.get('ids', {}).get('imdb')

        if not tmdb_id:
            self._log._add(
                'tv' if i_type == 'show' else 'movie', item.get('ids', {}).get('slug'),
                'skipped item in Trakt user list with missing TMDb ID')
            return

        return func(tmdb_id, force=force, imdb_id=imdb_id, user_slug=user_slug, list_slug=list_slug)
