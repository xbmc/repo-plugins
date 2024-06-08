from threading import Thread


CRONJOB_POLL_TIME = 600


class CronJobMonitor(Thread):

    _poll_time = CRONJOB_POLL_TIME

    def __init__(self, update_hour=0):
        from xbmc import Monitor
        Thread.__init__(self)
        self.exit = False
        self.update_hour = update_hour
        self.xbmc_monitor = Monitor()

    def _on_startup(self):
        self._do_delete_old_databases()
        self._do_recache_kodidb()
        self._do_trakt_authorization()

    def _on_poll(self):
        self._do_library_update_check()
        self._do_trakt_lastactivities_update()

    @property
    def trakt_api(self):
        try:
            return self._trakt_api
        except AttributeError:
            from tmdbhelper.lib.api.trakt.api import TraktAPI
            self._trakt_api = TraktAPI()
            return self._trakt_api

    @staticmethod
    def _do_delete_old_databases():
        from tmdbhelper.lib.script.method.maintenance import clean_old_databases
        clean_old_databases()

    @staticmethod
    def _do_recache_kodidb():
        from tmdbhelper.lib.script.method.maintenance import recache_kodidb
        recache_kodidb(notification=False)

    def _do_trakt_authorization(self):
        from jurialmunkey.parser import boolean
        from jurialmunkey.window import get_property
        self.trakt_api.authorize(confirmation=True)
        self.xbmc_monitor.waitForAbort(1)
        if not boolean(get_property('TraktIsAuth')):
            return
        from tmdbhelper.lib.script.method.trakt import get_stats
        get_stats()

    def _do_trakt_lastactivities_update(self):
        from jurialmunkey.parser import boolean
        from jurialmunkey.window import get_property
        if not boolean(get_property('TraktIsAuth')):
            return
        self.trakt_api.get_last_activity(cache_refresh=True)

    def _do_library_update(self):
        from tmdbhelper.lib.addon.plugin import executebuiltin
        from tmdbhelper.lib.addon.tmdate import get_datetime_now, get_timedelta
        executebuiltin('RunScript(plugin.video.themoviedb.helper,library_autoupdate)')
        executebuiltin(f'Skin.SetString(TMDbHelper.AutoUpdate.LastTime,{get_datetime_now().strftime("%Y-%m-%dT%H:%M:%S")})')
        self.library_update_next += get_timedelta(hours=24)  # Set next update for tomorrow

    def _do_library_update_check(self):
        from jurialmunkey.parser import try_int
        from tmdbhelper.lib.addon.tmdate import convert_timestamp, get_datetime_now, get_timedelta, get_datetime_today, get_datetime_time, get_datetime_combine
        from tmdbhelper.lib.addon.plugin import get_setting, get_infolabel
        if not get_setting('library_autoupdate'):
            return
        self.library_update_next = get_datetime_combine(get_datetime_today(), get_datetime_time(try_int(self.update_hour)))
        self.library_update_last = get_infolabel('Skin.String(TMDbHelper.AutoUpdate.LastTime)')
        self.library_update_last = convert_timestamp(self.library_update_last) if self.library_update_last else None

        # If we've already updated the library today then set a new next update time for tomorrow
        if self.library_update_last and self.library_update_last > self.library_update_next:
            self.library_update_next += get_timedelta(hours=24)

        # If the next update timestamp has elapsed then we should update the library
        if get_datetime_now() > self.library_update_next:
            self._do_library_update()

    def run(self):
        self._on_startup()

        while not self.xbmc_monitor.abortRequested() and not self.exit:
            self.xbmc_monitor.waitForAbort(self._poll_time)
            self._on_poll()

        del self.xbmc_monitor
