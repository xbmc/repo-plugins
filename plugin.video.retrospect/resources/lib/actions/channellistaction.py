# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmcgui
import xbmcplugin

from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.actions.actionparser import ActionParser
from resources.lib.retroconfig import Config
from resources.lib.actions import action


class ChannelListAction(AddonAction):
    def __init__(self, parameter_parser, category=None):
        """ Displays the channels that are currently available in XOT as a directory
        listing.

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        :param str category:                   The category to show channels for

        """

        super(ChannelListAction, self).__init__(parameter_parser)

        self.category = category

    def execute(self):
        if self.category:
            Logger.info("Plugin::show_channel_list for %s", self.category)
        else:
            Logger.info("Plugin::show_channel_list")
        try:
            # only display channels
            channel_register = ChannelIndex.get_register()
            channels = channel_register.get_channels()

            xbmc_items = []

            # Should we show the "All Favourites"?
            if AddonSettings.show_show_favourites_in_channel_list():
                icon = Config.icon
                fanart = Config.fanart
                name = LanguageHelper.get_localized_string(LanguageHelper.AllFavouritesId)
                kodi_item = xbmcgui.ListItem(name, name)

                # set art
                try:
                    kodi_item.setIconImage(icon)
                except:
                    # it was deprecated
                    pass
                kodi_item.setArt({'thumb': icon, 'icon': icon})
                kodi_item.setProperty(self._propertyRetrospect, "true")
                kodi_item.setProperty(self._propertyRetrospectCategory, "true")

                if not AddonSettings.hide_fanart():
                    kodi_item.setArt({'fanart': fanart})

                url = self.parameter_parser.create_action_url(
                    None, action=action.ALL_FAVOURITES)
                xbmc_items.append((url, kodi_item, True))

            for channel in channels:
                if self.category and channel.category != self.category:
                    Logger.debug("Skipping %s (%s) due to category filter", channel.channelName,
                                 channel.category)
                    continue

                # Get the Kodi item
                item = channel.get_kodi_item()
                item.setProperty(self._propertyRetrospect, "true")
                item.setProperty(self._propertyRetrospectChannel, "true")
                if channel.settings:
                    item.setProperty(self._propertyRetrospectChannelSetting, "true")
                if channel.adaptiveAddonSelectable:
                    item.setProperty(self._propertyRetrospectAdaptive, "true")

                # Get the context menu items
                context_menu_items = self._get_context_menu_items(channel)
                item.addContextMenuItems(context_menu_items)
                # Get the URL for the item
                url = self.parameter_parser.create_action_url(
                    channel, action=action.LIST_FOLDER)

                # Append to the list of Kodi Items
                xbmc_items.append((url, item, True))

            # Add the items
            ok = xbmcplugin.addDirectoryItems(self.handle, xbmc_items, len(xbmc_items))

            # Just let Kodi display the order we give.
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.setContent(handle=self.handle, content="tvshows")
            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            xbmcplugin.endOfDirectory(self.handle, False)
            Logger.critical("Error fetching channels for plugin", exc_info=True)
