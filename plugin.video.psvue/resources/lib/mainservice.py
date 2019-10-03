from globals import *
from database import Database
from guideservice import BuildGuide


class MainService:
    monitor = None
    last_update = None

    def __init__(self):
        self.monitor = xbmc.Monitor()

        self.db = Database()
        self.db.set_db_channels(get_channel_list())
        build_playlist(self.db.get_db_channels())

        xbmc.log('Calling BuildGuide to start....')
        self.guideservice = BuildGuide()
        self.guideservice.start()

        self.last_update = datetime.now()
        self.main_loop()

    def main_loop(self):
        while not self.monitor.abortRequested():
            # Sleep/wait for abort for 1 hour
            if self.monitor.waitForAbort(3600):
                # Abort was requested while waiting. We should exit
                break
            if self.last_update < datetime.now() - timedelta(days=1):
                self.db.set_db_channels(get_channel_list())
                build_playlist(self.db.get_db_channels())
                self.last_update = datetime.now()

            xbmc.log("PS Vue EPG Update Check. Last Update: " + self.last_update.strftime('%m/%d/%Y %H:%M:%S'),
                     level=xbmc.LOGNOTICE)

        self.close()

    def close(self):
        self.guideservice.stop()
        del self.monitor
