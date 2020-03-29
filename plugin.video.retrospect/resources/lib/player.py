# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmc

from resources.lib.logger import Logger


# noinspection PyPep8Naming
class Player(xbmc.Player):
    def __init__(self, show_subs=False, subs=None):
        """ Initialises a custom Player object to handle the wait for playback and stop

        :param bool show_subs:  Should we show subs be default
        :param list[str] subs:  A list of possible subtitles

        Currently only the first subtitle is added.

        """

        xbmc.Player.__init__(self)

        self.show_subs = show_subs
        self.subs = subs
        self.__monitor = xbmc.Monitor()
        self.__playBackEventsTriggered = False
        self.__playPlayBackEndedEventsTriggered = False
        self.__pollInterval = 1.0

    def waitForPlayBack(self, url=None, time_out=30):
        """ Blocks the call until playback is started.

        :param str url:         The url that should start playing
        :param int time_out:    Maximum time to wait.

        This method checks whether the playback started. If an url was specified, it will wait
        for that url to be the active one playing before returning.

        """

        Logger.debug("Player: Waiting for playback")
        if self.__is_url_playing(url):
            self.__playBackEventsTriggered = True
            Logger.debug("Player: Already Playing")
            return

        # noinspection PyTypeChecker
        for i in range(0, int(time_out / self.__pollInterval)):
            if self.__monitor.abortRequested():
                Logger.debug("Player: Abort requested (%s)", i * self.__pollInterval)
                return

            if self.__is_url_playing(url):
                Logger.debug("Player: PlayBack started (%s)", i * self.__pollInterval)
                return

            if self.__playPlayBackEndedEventsTriggered:
                Logger.warning("Player: PlayBackEnded triggered while waiting for start.")
                return

            self.__monitor.waitForAbort(self.__pollInterval)
            Logger.trace("Player: Waiting for an abort (%s)", i * self.__pollInterval)

        Logger.warning("Player: time-out occurred waiting for playback (%s)", time_out)
        return

    # The end of playback is 100% working, as a next track does not trigger any events.
    # def waitForPlayBackEnded(self):
    #     Logger.debug("Player: Waiting for playback to end")
    #
    #     while not self.__monitor.abortRequested() and not self.__playPlayBackEndedEventsTriggered:
    #         self.__monitor.waitForAbort(1)
    #         Logger.trace("Player: Waiting for an abort")
    #
    #     if self.__monitor.abortRequested():
    #         Logger.debug("Player: Abort requested")
    #     else:
    #         Logger.debug("Player: PlayBacked ended")

    # region Kodi call-back functions
    def onAVStarted(self):
        """ Will be called when Kodi has a video or audiostream """

        Logger.trace("Player: [onAVStarted] called")

        if self.subs:
            Logger.debug("Player: Setting subtitle: %s", self.subs[0])
            self.setSubtitles(self.subs[0])

        Logger.debug("Player: Showing subtitles")
        self.showSubtitles(self.show_subs)
        self.__playback_started()

    def onPlayBackEnded(self):
        """ Will be called when [Kodi] stops playing a file """

        Logger.trace("Player: [onPlayBackEnded] called")
        self.__playback_stopped()

    def onPlayBackStopped(self):
        """ Will be called when [user] stops Kodi playing a file """

        Logger.trace("Player: [onPlayBackStopped] called")
        self.__playback_stopped()

    def onPlayBackError(self):
        """ Will be called when playback stops due to an error. """

        Logger.trace("Player: [onPlayBackError] called")
        self.__playback_stopped()

    # Triggered both on stop and start
    # def onAVChange(self):
    #     Logger.trace("Player: [onAVChange] called")
    #
    #     self.__playBackEventsTriggered = False
    #     self.__playPlayBackEndedEventsTriggered = True
    # endregion

    def __playback_stopped(self):
        """ Sets the correct flags after playback stopped """

        self.__playBackEventsTriggered = False
        self.__playPlayBackEndedEventsTriggered = True

    def __playback_started(self):
        """ Sets the correct flags after playback started """

        self.__playBackEventsTriggered = True
        self.__playPlayBackEndedEventsTriggered = False

    def __is_url_playing(self, url):
        """ Checks whether the given url is playing

        :param str url: The url to check for playback.

        :return: Indication if the url is actively playing or not.
        :rtype: bool

        """

        if not self.isPlaying():
            Logger.trace("Player: Not playing")
            return False

        if not self.__playBackEventsTriggered:
            Logger.trace("Player: Playing but the Kodi events did not yet trigger")
            return False

        # We are playing
        if url is None or url.startswith("plugin://"):
            Logger.trace("Player: No valid URL to check playback against: %s", url)
            return True

        playing_file = self.getPlayingFile()
        Logger.trace("Player: Checking \n'%s' vs \n'%s'", url, playing_file)
        return url == playing_file
