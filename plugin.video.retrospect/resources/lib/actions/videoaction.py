# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import xbmc
import xbmcplugin

from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.chn_class import Channel
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.locker import LockWithDialog
from resources.lib.logger import Logger
from resources.lib.actions.actionparser import ActionParser
from resources.lib.xbmcwrapper import XbmcWrapper


class VideoAction(AddonAction):
    def __init__(self, parameter_parser, channel):
        """ Starts the videoitem using a playlist.

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param Channel channel:                The channel info for the channel

        """

        super(VideoAction, self).__init__(parameter_parser)

        if channel is None:
            raise ValueError("No Channel specified for video to play")
        if parameter_parser.media_item is None:
            raise ValueError("No MediaItem to play")

        self.__channel = channel
        self.__media_item = parameter_parser.media_item

    def execute(self):
        from resources.lib import player

        Logger.debug("Playing videoitem using PlayListMethod")

        try:
            media_item = self.__media_item

            if not media_item.complete:
                media_item = self.__channel.process_video_item(media_item)

            # Any warning to show
            self.__show_warnings(media_item)

            # validated the updated media_item
            if not media_item.complete or not media_item.has_media_item_parts():
                Logger.warning(
                    "process_video_item returned an MediaItem that had MediaItem.complete = False:\n%s",
                    media_item)

            if not media_item.has_media_item_parts():
                # the update failed or no items where found. Don't play
                XbmcWrapper.show_notification(
                    LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                    LanguageHelper.get_localized_string(LanguageHelper.NoStreamsId),
                    XbmcWrapper.Error)
                Logger.warning("Could not start playback due to missing streams. Item:\n%s",
                               media_item)
                xbmcplugin.endOfDirectory(self.handle, False)
                return

            kodi_items = media_item.get_kodi_play_list_data(
                AddonSettings.get_max_stream_bitrate(self.__channel),
                self.__channel.proxy
            )

            Logger.debug("Continuing playback in plugin.py")
            if not bool(kodi_items):
                Logger.warning("play_video_item did not return valid playdata")
                xbmcplugin.endOfDirectory(self.handle, False)
                return

            # Now we force the busy dialog to close, else the video will not play and the
            # setResolved will not work.
            LockWithDialog.close_busy_dialog()

            # Append it to the Kodi playlist in a smart way.
            start_url = self.__append_kodi_play_list(kodi_items)

            # Set the mode (if the InputStream Adaptive add-on is used, we also need to set it)
            show_subs = AddonSettings.show_subtitles()

            # TODO: Apparently if we use the InputStream Adaptive, using the setSubtitles() causes sync issues.
            available_subs = [p.Subtitle for p in media_item.MediaItemParts]

            # Get the Kodi Player instance (let Kodi decide what player, see
            # http://forum.kodi.tv/showthread.php?tid=173887&pid=1516662#pid1516662)
            kodi_player = player.Player(show_subs=show_subs, subs=available_subs)
            kodi_player.waitForPlayBack(url=start_url, time_out=10)

            xbmcplugin.endOfDirectory(self.handle, True)
        except:
            XbmcWrapper.show_notification(
                LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                LanguageHelper.get_localized_string(LanguageHelper.NoPlaybackId),
                XbmcWrapper.Error)
            Logger.critical("Could not playback the url", exc_info=True)

            # We need to single Kodi that it failed and it should not wait longer. Either using a
            # `raise` or with `xbmcplugin.endOfDirectory`. Doing the latter for now although we are
            # not really playing.
            xbmcplugin.endOfDirectory(self.handle, False)

        return

    def __show_warnings(self, media_item):
        """ Show playback warnings for this MediaItem

        :param MediaItem media_item: The current MediaItem that will be played.

        """

        if (media_item.isDrmProtected or media_item.isPaid) and AddonSettings.show_drm_paid_warning():
            if media_item.isDrmProtected:
                Logger.debug("Showing DRM Warning message")
                title = LanguageHelper.get_localized_string(LanguageHelper.DrmTitle)
                message = LanguageHelper.get_localized_string(LanguageHelper.DrmText)
                XbmcWrapper.show_dialog(title, message)
            elif media_item.isPaid:
                Logger.debug("Showing Paid Warning message")
                title = LanguageHelper.get_localized_string(LanguageHelper.PaidTitle)
                message = LanguageHelper.get_localized_string(LanguageHelper.PaidText)
                XbmcWrapper.show_dialog(title, message)

    def __append_kodi_play_list(self, kodi_items):
        # Get the current playlist
        play_list = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        play_list_size = play_list.size()
        start_index = play_list.getposition()  # the current location
        if start_index < 0:
            start_index = 0
        Logger.debug("Current playlist size and position: %s @ %s", play_list_size, start_index)

        current_play_list_items = [play_list[i] for i in range(0, len(play_list))]
        play_list.clear()
        for i in range(0, start_index):
            Logger.debug("Adding existing PlayList item")
            play_list.add(current_play_list_items[i].getPath(), current_play_list_items[i])

        # The current item to play (we need to store te starting url for later)
        Logger.debug("Adding Main PlayList item")
        kodi_item, start_url = kodi_items.pop(0)
        play_list.add(start_url, kodi_item, start_index)
        xbmcplugin.setResolvedUrl(self.handle, True, kodi_item)

        # now we add the rest of the Kodi ListItems for the other parts
        for kodi_item, stream_url in kodi_items:
            Logger.debug("Adding Additional PlayList item")
            play_list.add(stream_url, kodi_item, start_index)
            xbmcplugin.setResolvedUrl(self.handle, True, kodi_item)

        # add the remaining items
        for i in range(start_index + 1, len(current_play_list_items)):
            Logger.debug("Adding existing PlayList item")
            play_list.add(current_play_list_items[i].getPath(), current_play_list_items[i])

        return start_url
