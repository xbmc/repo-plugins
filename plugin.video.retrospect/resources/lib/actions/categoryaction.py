# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import xbmcgui
import xbmcplugin

from resources.lib.actions import action
from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.retroconfig import Config


class CategoryAction(AddonAction):
    def __init__(self, parameter_parser):
        """ Displays the channels that are currently available in XOT as a directory
        listing.

        :param ActionParser parameter_parser:  A ActionParser object to is used to parse
                                                and create urls
        """

        super(CategoryAction, self).__init__(parameter_parser)

    def execute(self):
        """ Displays the show_categories that are currently available in XOT as a directory
        listing.

        :return: indication if all succeeded.
        :rtype: bool

        """

        Logger.info("Plugin::show_categories")
        channel_register = ChannelIndex.get_register()
        categories = channel_register.get_categories()

        kodi_items = []
        icon = Config.icon
        fanart = Config.fanart
        for category in categories:
            name = LanguageHelper.get_localized_category(category)
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
                None, action=action.LIST_CATEGORY, category=category)
            kodi_items.append((url, kodi_item, True))

        # Logger.Trace(kodi_items)
        ok = xbmcplugin.addDirectoryItems(self.handle, kodi_items, len(kodi_items))
        xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(self.handle, ok)
        return ok
