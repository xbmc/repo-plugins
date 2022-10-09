from resources.lib.files.futils import dumps_to_file, del_old_files
from resources.lib.addon.tmdate import get_todays_date


LOG_FOLDER = 'log_library'


class _LibraryLogger():
    def __init__(self):
        self.logging = {}

    def _log_item(self, key, tmdb_id, season=None, episode=None, **kwargs):
        to_update = self.logging.setdefault(key, {})
        to_update = self.logging[key].setdefault(tmdb_id, {})
        if season is not None:
            to_update = self.logging[key][tmdb_id].setdefault('seasons', {})
            to_update = self.logging[key][tmdb_id]['seasons'].setdefault(season, {})
        if episode is not None:
            to_update = self.logging[key][tmdb_id]['seasons'][season].setdefault('episodes', {})
            to_update = self.logging[key][tmdb_id]['seasons'][season]['episodes'].setdefault(episode, {})
        for k, v in kwargs.items():
            to_update[k] = v

    def _add(self, key, tmdb_id, log_msg, season=None, episode=None, **kwargs):
        if not log_msg:
            return
        self._log_item(key, tmdb_id, season=season, episode=episode, log_msg=log_msg, **kwargs)
        return log_msg

    def _out(self):  # TODO: Check logging value
        filename = f'{get_todays_date(str_fmt="%Y-%m-%d-%H%M%S")}.json'
        dumps_to_file(self.logging, LOG_FOLDER, filename)

    def _clean(self, limit=5):
        del_old_files(LOG_FOLDER, limit=limit)
