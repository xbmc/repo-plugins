from bossanova808.logger import Logger
from resources.lib.store import Store
import xbmc
import json


class KodiEventMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        Logger.debug('KodiEventMonitor __init__')

    def onSettingsChanged(self):
        Logger.info('onSettingsChanged - reload them.')
        Store.load_config_from_settings()

    # noinspection PyMethodMayBeStatic
    def onAbortRequested(self):
        Logger.debug('onAbortRequested')

    def onNotification(self, sender, method, data):
        if method == 'Player.OnStop':
            data = json.loads(data)
            Logger.debug("Notification:")
            Logger.debug(data)
