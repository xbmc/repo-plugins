from xbmc import Monitor
from resources.lib.addon.parser import try_int
from threading import Thread
from resources.lib.addon.tmdate import convert_timestamp, get_datetime_now, get_timedelta, get_datetime_today, get_datetime_time, get_datetime_combine
from resources.lib.addon.plugin import get_setting, executebuiltin, get_infolabel, set_setting


def update_skinshortcuts():
    """ Once-off routine to update skinshortcuts to append new widget reload affix """
    if get_setting('update_skinshortcuts'):
        return
    from resources.lib.files.futils import validate_join, get_files_in_folder, read_file, write_file
    from resources.lib.addon.consts import PARAM_WIDGETS_RELOAD, PARAM_WIDGETS_RELOAD_REPLACE
    folder = validate_join('special://profile/addon_data/', 'script.skinshortcuts/')
    files = get_files_in_folder(folder, regex=r".*\.(xml|properties)$")
    affix = PARAM_WIDGETS_RELOAD
    subst = PARAM_WIDGETS_RELOAD_REPLACE
    for f in files:
        filename = validate_join(folder, f)
        filemeta = read_file(filename)
        fileline = filemeta.split('\n')
        for x, i in enumerate(fileline):
            if subst in i:
                i.replace(subst, affix)
            if affix in i:
                continue
            if 'plugin://plugin.video.themoviedb.helper/' not in i:
                continue
            if '&widget=true' in i:
                fileline[x] = i.replace('&widget=true', f'&widget=true&{affix}')
                continue
            if '&amp;widget=true' in i:
                fileline[x] = i.replace('&amp;widget=true', f'&amp;widget=true&amp;{affix}')
                continue
        filemeta = '\n'.join(fileline)
        write_file(filemeta, filename)
    set_setting('update_skinshortcuts', True)


def clean_old_databases():
    """ Once-off routine to delete old unused database versions to avoid wasting disk space """
    from resources.lib.files.futils import delete_folder
    for f in ['database', 'database_v2', 'database_v3', 'database_v4']:
        delete_folder(f, force=True, check_exists=True)


class CronJobMonitor(Thread):
    def __init__(self, update_hour=0):
        Thread.__init__(self)
        self.exit = False
        self.poll_time = 1800  # Poll every 30 mins since we don't need to get exact time for update
        self.update_hour = update_hour
        self.xbmc_monitor = Monitor()

    def run(self):
        update_skinshortcuts()
        clean_old_databases()

        self.xbmc_monitor.waitForAbort(600)  # Wait 10 minutes before doing updates to give boot time
        if self.xbmc_monitor.abortRequested():
            del self.xbmc_monitor
            return

        self.next_time = get_datetime_combine(get_datetime_today(), get_datetime_time(try_int(self.update_hour)))  # Get today at hour
        self.last_time = get_infolabel('Skin.String(TMDbHelper.AutoUpdate.LastTime)')  # Get last update
        self.last_time = convert_timestamp(self.last_time) if self.last_time else None
        if self.last_time and self.last_time > self.next_time:
            self.next_time += get_timedelta(hours=24)  # Already updated today so set for tomorrow

        while not self.xbmc_monitor.abortRequested() and not self.exit and self.poll_time:
            if get_setting('library_autoupdate'):
                if get_datetime_now() > self.next_time:  # Scheduled time has past so lets update
                    executebuiltin('RunScript(plugin.video.themoviedb.helper,library_autoupdate)')
                    executebuiltin(f'Skin.SetString(TMDbHelper.AutoUpdate.LastTime,{get_datetime_now().strftime("%Y-%m-%dT%H:%M:%S")})')
                    self.next_time += get_timedelta(hours=24)  # Set next update for tomorrow
            self.xbmc_monitor.waitForAbort(self.poll_time)

        del self.xbmc_monitor
