import xbmc
from resources.lib.addon.parser import try_int
from threading import Thread
from resources.lib.addon.plugin import ADDON
from resources.lib.addon.timedate import convert_timestamp, get_datetime_now, get_timedelta, get_datetime_today, get_datetime_time, get_datetime_combine


class CronJobMonitor(Thread):
    def __init__(self, update_hour=0):
        Thread.__init__(self)
        self.exit = False
        self.poll_time = 1800  # Poll every 30 mins since we don't need to get exact time for update
        self.update_hour = update_hour
        self.xbmc_monitor = xbmc.Monitor()

    def run(self):
        self.xbmc_monitor.waitForAbort(600)  # Wait 10 minutes before doing updates to give boot time
        if self.xbmc_monitor.abortRequested():
            del self.xbmc_monitor
            return

        self.next_time = get_datetime_combine(get_datetime_today(), get_datetime_time(try_int(self.update_hour)))  # Get today at hour
        self.last_time = xbmc.getInfoLabel('Skin.String(TMDbHelper.AutoUpdate.LastTime)')  # Get last update
        self.last_time = convert_timestamp(self.last_time) if self.last_time else None
        if self.last_time and self.last_time > self.next_time:
            self.next_time += get_timedelta(hours=24)  # Already updated today so set for tomorrow

        while not self.xbmc_monitor.abortRequested() and not self.exit and self.poll_time:
            if ADDON.getSettingBool('library_autoupdate'):
                if get_datetime_now() > self.next_time:  # Scheduled time has past so lets update
                    xbmc.executebuiltin('RunScript(plugin.video.themoviedb.helper,library_autoupdate)')
                    xbmc.executebuiltin('Skin.SetString(TMDbHelper.AutoUpdate.LastTime,{})'.format(get_datetime_now().strftime("%Y-%m-%dT%H:%M:%S")))
                    self.next_time += get_timedelta(hours=24)  # Set next update for tomorrow
            self.xbmc_monitor.waitForAbort(self.poll_time)

        del self.xbmc_monitor
