# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import xbmc
import xbmcgui

# we need to import the initializer
addOnPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(addOnPath)

# setup some initial stuff
from resources.lib.initializer import Initializer
Initializer.set_unicode()

from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
Logger.create_logger(os.path.join(Config.profileDir, Config.logFileNameAddon),
                     Config.appName,
                     append=True,
                     dual_logger=lambda x, y=4: xbmc.log(x, y))

from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.favourites import Favourites
from resources.lib.actions.actionparser import ActionParser
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.locker import LockWithDialog
from resources.lib.cloaker import Cloaker
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.actions import keyword
from resources.lib.actions import action

Logger.instance().minLogLevel = AddonSettings.get_log_level()


class Menu(ActionParser):

    def __init__(self, menu_action):
        Logger.info("**** Starting menu '%s' for %s add-on version %s ****",
                    menu_action, Config.appName, Config.version)

        # noinspection PyUnresolvedReferences
        self.kodiItem = sys.listitem

        params = self.kodiItem.getPath()
        if not params:
            self.channelObject = None
            return

        name, params = params.split("?", 1)
        params = "?{0}".format(params)

        # Main constructor parses
        super(Menu, self).__init__(name, -1, params)

        self.channelObject = self.__get_channel()
        Logger.debug(self)

    def hide_channel(self):
        """ Hides a specific channel """

        Logger.info("Hiding channel: %s", self.channelObject)
        AddonSettings.set_channel_visibility(self.channelObject, False)
        self.refresh()

    def select_channels(self):
        """ Selects the channels that should be visible.

        @return: None
        """

        valid_channels = ChannelIndex.get_register().get_channels(include_disabled=True)
        channels_to_show = [c for c in valid_channels if c.visible]
        # The old way
        # channels_to_show = filter(lambda c: c.visible, valid_channels)

        selected_channels = [c for c in channels_to_show if c.enabled]
        selected_indices = list([channels_to_show.index(c) for c in selected_channels])
        Logger.debug("Currently selected channels: %s", selected_indices)

        channel_to_show_names = [HtmlEntityHelper.convert_html_entities(c.channelName) for c in channels_to_show]
        # The old way
        # channel_to_show_names = list(map(lambda c: HtmlEntityHelper.convert_html_entities(c.channelName), channels_to_show))

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.get_localized_string(LanguageHelper.ChannelSelection)[:-1]
        selected_channels = dialog.multiselect(heading, channel_to_show_names,
                                               preselect=selected_indices)
        if selected_channels is None:
            return

        selected_channels = list(selected_channels)
        Logger.debug("New selected channels:       %s", selected_channels)

        indices_to_remove = [i for i in selected_indices if i not in selected_channels]
        indices_to_add = [i for i in selected_channels if i not in selected_indices]
        for i in indices_to_remove:
            Logger.info("Hiding channel: %s", channels_to_show[i])
            AddonSettings.set_channel_visibility(channels_to_show[i], False)

        for i in indices_to_add:
            Logger.info("Showing channel: %s", channels_to_show[i])
            AddonSettings.set_channel_visibility(channels_to_show[i], True)

        self.refresh()
        return

    def show_country_settings(self):
        """ Shows the country settings page where channels can be shown/hidden based on the
        country of origin. """

        if AddonSettings.is_min_version(AddonSettings.KodiLeia):
            AddonSettings.show_settings(-99)
        else:
            AddonSettings.show_settings(101)
        self.refresh()

    def show_settings(self):
        """ Shows the add-on settings page and refreshes when closing it. """

        AddonSettings.show_settings()
        self.refresh()

    def channel_settings(self):
        """ Shows the channel settings for the selected channel. Refreshes the list after closing
        the settings. """

        AddonSettings.show_channel_settings(self.channelObject)
        self.refresh()

    def favourites(self, all_favorites=False):
        """ Shows the favourites, either for a channel or all that are known.

        @param all_favorites: if True the list will return all favorites. Otherwise it will only
                              only return the channel ones.

        """

        # it's just the channel, so only add the favourites
        cmd_url = self.create_action_url(
            None if all_favorites else self.channelObject,
            action=action.ALL_FAVOURITES if all_favorites else action.CHANNEL_FAVOURITES
        )

        xbmc.executebuiltin("Container.Update({0})".format(cmd_url))

    @LockWithDialog(logger=Logger.instance())
    def add_favourite(self):
        """ Adds the selected item to the favourites. The opens the favourite list. """

        # remove the item
        item = self.media_item

        # no need for dates in the favourites
        # item.clear_date()
        Logger.debug("Adding favourite: %s", item)

        f = Favourites(Config.favouriteDir)
        if item.is_playable:
            action_value = action.PLAY_VIDEO
        else:
            action_value = action.LIST_FOLDER

        # add the favourite
        f.add(self.channelObject,
              item,
              self.create_action_url(self.channelObject, action_value, item))

        # we are finished, so just open the Favorites
        self.favourites()

    @LockWithDialog(logger=Logger.instance())
    def remove_favourite(self):
        """ Remove the selected favourite and then refresh the favourite list. """

        # remove the item
        item = self.media_item
        Logger.debug("Removing favourite: %s", item)
        f = Favourites(Config.favouriteDir)
        f.remove(item)

        # refresh the list
        self.refresh()

    def refresh(self):
        """ Refreshes the current Kodi list """
        xbmc.executebuiltin("Container.Refresh()")

    def toggle_cloak(self):
        """ Toggles the cloaking (showing/hiding) of the selected folder. """

        item = self.media_item
        Logger.info("Cloaking current item: %s", item)
        c = Cloaker(self.channelObject, AddonSettings.store(LOCAL), logger=Logger.instance())

        if c.is_cloaked(item.url):
            c.un_cloak(item.url)
            self.refresh()
            return

        first_time = c.cloak(item.url)
        if first_time:
            XbmcWrapper.show_dialog(LanguageHelper.get_localized_string(LanguageHelper.CloakFirstTime),
                                    LanguageHelper.get_localized_string(LanguageHelper.CloakMessage))

        del c
        self.refresh()

    def set_bitrate(self):
        """ Sets the bitrate for the selected channel via a specific dialog. """

        if self.channelObject is None:
            raise ValueError("Missing channel")

        # taken from the settings.xml
        bitrate_options = "Retrospect|0|100|250|500|750|1000|1500|2000|2500|4000|8000|20000"\
            .split("|")

        current_bitrate = AddonSettings.get_max_channel_bitrate(self.channelObject)
        Logger.debug("Found bitrate for %s: %s", self.channelObject, current_bitrate)
        current_bitrate_index = 0 if current_bitrate not in bitrate_options \
            else bitrate_options.index(current_bitrate)

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.get_localized_string(LanguageHelper.BitrateSelection)
        selected_bitrate = dialog.select(heading, bitrate_options,
                                         preselect=current_bitrate_index)
        if selected_bitrate < 0:
            return

        Logger.info("Changing bitrate for %s from %s to %s",
                    self.channelObject,
                    bitrate_options[current_bitrate_index],
                    bitrate_options[selected_bitrate])

        AddonSettings.set_max_channel_bitrate(self.channelObject,
                                              bitrate_options[selected_bitrate])
        return

    def set_inputstream_adaptive(self):
        """ Set the InputStream Adaptive for this channel """

        if self.channelObject is None:
            raise ValueError("Missing channel")

        if not self.channelObject.adaptiveAddonSelectable:
            Logger.warning("Cannot set InputStream Adaptive add-on mode for %s", self.channelObject)
            return

        current_mode = AddonSettings.get_adaptive_mode(self.channelObject)
        mode_values = [None, True, False]
        current_index = mode_values.index(current_mode)
        mode_options = [
            LanguageHelper.get_localized_string(LanguageHelper.Retrospect),
            LanguageHelper.get_localized_string(LanguageHelper.Enabled),
            LanguageHelper.get_localized_string(LanguageHelper.Disabled)
        ]

        dialog = xbmcgui.Dialog()
        heading = LanguageHelper.get_localized_string(LanguageHelper.ChannelAdaptiveMode)
        selected_index = dialog.select(heading, mode_options, preselect=current_index)
        if selected_index < 0:
            return
        selected_value = mode_values[selected_index]

        Logger.info("Changing InputStream Adaptive mode for %s from %s to %s",
                    self.channelObject,
                    mode_options[current_index],
                    mode_options[selected_index])

        AddonSettings.set_adaptive_mode(self.channelObject, selected_value)

        # Refresh if we have a video item selected, so the cached urls are removed.
        if keyword.PICKLE in self.params:
            Logger.debug("Refreshing list to clear URL caches")
            self.refresh()

    def __get_channel(self):
        channel_url_id = self.params.get(keyword.CHANNEL, None)
        channel_code = self.params.get(keyword.CHANNEL_CODE, None)
        if not channel_url_id:
            return None

        Logger.debug("Fetching channel %s - %s", channel_url_id, channel_code)
        channel = ChannelIndex.get_register().get_channel(channel_url_id, channel_code, info_only=True)
        Logger.debug("Created channel: %s", channel)
        return channel

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            Logger.critical("Error in menu handling: %s", str(exc_val), exc_info=True)

        # make sure we leave no references behind
        AddonSettings.clear_cached_addon_settings_object()
        # close the log to prevent locking on next call
        Logger.instance().close_log()
        return False
