import xbmc
import xbmcaddon

# service class
ampache = xbmcaddon.Addon("plugin.audio.ampache")

from resources.lib.utils import get_objectId_from_fileURL


class AmpacheMonitor(xbmc.Monitor):
    # Monitor for Ampache service events

    onPlay = False

    def __init__(self):
        xbmc.log("AmpacheMonitor::ServiceMonitor called", xbmc.LOGDEBUG)

    # start mainloop
    def run(self):
        while not self.abortRequested():
            if self.waitForAbort(1):
                # Abort was requested while waiting. We should exit
                break

    def close(self):
        pass

    def onNotification(self, sender, method, data):
        xbmc.log(
            "AmpacheMonitor::onNotification called - method: %s, sender: %s"
            % (method, sender),
            xbmc.LOGDEBUG,
        )

        if not sender or not method or not data:
            xbmc.log("AmpacheMonitor::Invalid notification data", xbmc.LOGWARNING)
            return

        # a little hack to avoid calling rate every time a song start
        if method == "Player.OnStop":
            self.onPlay = False
            xbmc.log("AmpacheMonitor::onPlay status changed to False", xbmc.LOGDEBUG)
        elif method == "Player.OnPlay":
            self.onPlay = True
            xbmc.log("AmpacheMonitor::onPlay status changed to True", xbmc.LOGDEBUG)
        elif method == "Info.OnChanged" and self.onPlay:
            if xbmc.Player().isPlaying():
                try:
                    file_url = xbmc.Player().getPlayingFile()
                    if not file_url:
                        xbmc.log(
                            "AmpacheMonitor::No playing file, skipping", xbmc.LOGDEBUG
                        )
                        return

                    if not get_objectId_from_fileURL(file_url):
                        xbmc.log(
                            "AmpacheMonitor::No object ID found in URL, skipping",
                            xbmc.LOGDEBUG,
                        )
                        return

                    xbmc.log(
                        "AmpacheMonitor::Starting setRating for URL: %s" % file_url,
                        xbmc.LOGDEBUG,
                    )
                    xbmc.executebuiltin(
                        "RunPlugin(plugin://plugin.audio.ampache/?mode=205)"
                    )
                except ValueError as e:
                    xbmc.log("AmpacheMonitor::Value error: %s" % str(e), xbmc.LOGDEBUG)
                except Exception as e:
                    xbmc.log(
                        "AmpacheMonitor::Error in onNotification: %s" % repr(e),
                        xbmc.LOGERROR,
                    )
