import xbmc

from bossanova808.constants import HOME_WINDOW
from bossanova808.logger import Logger
from resources.lib.playback import Playback

from resources.lib.store import Store


class KodiPlayer(xbmc.Player):
    """
    This class represents/monitors the Kodi video player
    """

    # noinspection PyUnusedLocal
    def __init__(self, *args):
        xbmc.Player.__init__(self)
        Logger.debug('Player __init__')

    # Use on AVStarted (vs Playback started) we want to record a playback only if the user actually _saw_ a video...
    def onAVStarted(self):
        Logger.info('onAVStarted')

        # KISS - only support video...
        if xbmc.getCondVisibility('Player.HasVideo'):

            # (If only we could just serialise a Kodi ListItem...)
            item = self.getPlayingItem()
            file = self.getPlayingFile()

            # If the current playback was Switchback-triggered from a Kodi ListItem,
            # retrieve the previously recorded Playback details from the list. Set the Home Window properties that have not yet been set.
            if item.getProperty('Switchback') or HOME_WINDOW.getProperty('Switchback'):
                Logger.info("Switchback triggered playback, so attempting to find and re-use existing Playback object")
                Logger.debug("Home Window property is:", HOME_WINDOW.getProperty('Switchback'))
                Logger.debug("ListItem property is:", item.getProperty('Switchback'))
                path_to_find = HOME_WINDOW.getProperty('Switchback') or item.getProperty('Switchback') or item.getPath()
                Store.current_playback = Store.switchback.find_playback_by_path(path_to_find)
                if Store.current_playback:
                    Logger.info("Found.  Re-using previously stored Playback object:", Store.current_playback)
                    # We won't have access to the listitem once playback is finishes, so set a property now so it can be used/cleared in onPlaybackFinished below
                    Store.update_home_window_switchback_property(Store.current_playback.path)
                    return
                else:
                    Logger.error("Switchback triggered playback, but no playback found in the list for this path - this shouldn't happen?!", path_to_find)

            # If we got to here, this was not a Switchback-triggered playback, or for some reason we've been unable to find the Playback.
            # Create a new Playback object and record the details.
            Logger.info("Not a Switchback playback, or error retrieving previous Playback, so creating a new Playback object to record details")
            Store.current_playback = Playback()
            Store.current_playback.update_playback_details(file, item)

    # Playback finished 'naturally'
    def onPlayBackEnded(self):
        self.onPlaybackFinished()

    # User stopped playback
    def onPlayBackStopped(self):
        self.onPlaybackFinished()

    @staticmethod
    def onPlaybackFinished():
        """
        Playback has finished - we need to update the PlaybackList and save it to file, and, if the user desires, force Kodi to browse to the appropriate show/season

        :return:
        """
        if not Store.current_playback or not Store.current_playback.path:
            Logger.error("onPlaybackFinished with no current playback details available?! ...not recording this playback")
            return

        Store.switchback.load_or_init()

        Logger.debug("onPlaybackFinished with Store.current_playback:")
        Logger.debug(Store.current_playback)
        Logger.debug("onPlaybackFinished with Store.switchback.list:")
        Logger.debug(Store.switchback.list)

        # Was this a Switchback-initiated playback?
        # (This property was set above in onAVStarted if the ListItem property was set, or explicitly in the PVR HACK! section in switchback_plugin.py this we only need to test for this)
        switchback_playback = HOME_WINDOW.getProperty('Switchback')
        # Clear the property if set, now playback has finished
        HOME_WINDOW.clearProperty('Switchback')

        # If we Switchbacked to a library episode, force Kodi to browse to the Show/Season
        # (NB it is not possible to force Kodi to go to movies and focus a specific movie as far as I can determine)
        if Store.episode_force_browse and switchback_playback:
            if Store.current_playback.type == "episode" and Store.current_playback.source == "kodi_library":
                Logger.info("Force browsing to tvshow/season of just finished playback")
                Logger.debug(f'flatten tvshows {Store.flatten_tvshows} totalseasons {Store.current_playback.totalseasons} dbid {Store.current_playback.dbid} tvshowdbid {Store.current_playback.tvshowdbid}')
                # Default: Browse to the show
                window = f'videodb://tvshows/titles/{Store.current_playback.tvshowdbid}'
                # 0 = Never flatten → browse to show root
                # 1 = If only one season → browse to season only when there are multiple seasons
                # 2 = Always flatten → browse to season
                if Store.flatten_tvshows == 2:
                    window += f'/{Store.current_playback.season}'
                elif Store.flatten_tvshows == 1 and (Store.current_playback.totalseasons or 0) > 1:
                    window += f'/{Store.current_playback.season}'
                xbmc.executebuiltin(f'ActivateWindow(Videos,{window},return)')

        # This rather long-winded approach is used to keep ALL the details recorded from the original playback
        # (in case they don't make it through when the playback is Switchback initiated - as sometimes seems to be the case)
        playback_to_remove = Store.switchback.find_playback_by_path(Store.current_playback.path)
        if playback_to_remove:
            Logger.debug("Updating Playback and list order")
            # Remove it from its current position
            Store.switchback.list.remove(playback_to_remove)
            # Update with the current playback times
            if Store.current_playback.source != "pvr_live":
                playback_to_remove.update({'resumetime': Store.current_playback.resumetime, 'totaltime': Store.current_playback.totaltime})
            # Re-insert at the top of the list
            Store.switchback.list.insert(0, playback_to_remove)
        else:
            Store.switchback.list.insert(0, Store.current_playback)

        # Trim the list to the max length
        Store.switchback.list = Store.switchback.list[0:Store.maximum_list_length]
        # Finally, save the updated PlaybackList
        Store.switchback.save_to_file()
        Logger.debug("Saved updated Store.switchback.list:", Store.switchback.list)

        # & make sure the context menu items are updated
        Store.update_switchback_context_menu()

        # And update the current view so if we're in the Switchback plugin listing, it gets refreshed
        # Use a delayed refresh to ensure Kodi has fully returned to the listing - but don't block, use threading
        def delayed_refresh():
            xbmc.sleep(200)  # Wait 200ms for UI to settle
            xbmc.executebuiltin("Container.Refresh")

        import threading
        threading.Thread(target=delayed_refresh).start()

        # ALTERNATIVE, but behaviour is slower/more visually janky
        # xbmc.executebuiltin('AlarmClock(SwitchbackRefresh,Container.Refresh,00:00:01,silent)')
