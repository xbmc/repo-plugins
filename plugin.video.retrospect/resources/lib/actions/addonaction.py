# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.chn_class import Channel
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.actions.actionparser import ActionParser


class AddonAction(object):
    __methodContainer = dict()  # : storage for the inspect.getmembers(channel) method. Improves performance

    def __init__(self, parameter_parser):
        """ Base class for add-on actions

        :param ActionParser parameter_parser:  a ActionParser object to is used to parse and
                                                   create urls

        """

        self._propertyRetrospect = "Retrospect"
        self._propertyRetrospectChannel = "RetrospectChannel"
        self._propertyRetrospectChannelSetting = "RetrospectChannelSettings"
        self._propertyRetrospectFolder = "RetrospectFolder"
        self._propertyRetrospectVideo = "RetrospectVideo"
        self._propertyRetrospectCloaked = "RetrospectCloaked"
        self._propertyRetrospectCategory = "RetrospectCategory"
        self._propertyRetrospectFavorite = "RetrospectFavorite"
        self._propertyRetrospectAdaptive = "RetrospectAdaptive"

        self.parameter_parser = parameter_parser
        if self.parameter_parser is None:
            raise ValueError("Missing ActionParser")

        self.handle = self.parameter_parser.handle

    def execute(self):
        raise NotImplementedError

    def _get_context_menu_items(self, channel, item=None):
        """ Retrieves the custom context menu items to display.

        :param Channel|None channel:    The channel from which to get the context menu items.
                                         The channel might be None in case of some actions that
                                         do not require a channel.
        :param MediaItem|None item:     The item to which the context menu belongs.

        :return: A list of context menu names and their commands.
        :rtype: list[tuple[str,str]]

        """

        context_menu_items = []

        # Generic, none-Python menu items that would normally cause an unwanted reload of the
        # Python interpreter instance within Kodi.
        refresh = LanguageHelper.get_localized_string(LanguageHelper.RefreshListId)
        context_menu_items.append((refresh, 'Container.Refresh()'))

        if item is None:
            return context_menu_items

        # if it was a favourites list, don't add the channel methods as they might be from a different channel
        if channel is None:
            return context_menu_items

        if item.has_info():
            info_action = LanguageHelper.get_localized_string(LanguageHelper.ItemInfo)
            context_menu_items.append((info_action, 'Action(info)'))

        # now we process the other items
        possible_methods = self.__get_members(channel)
        # Logger.Debug(possible_methods)

        for menu_item in channel.contextMenuItems:
            # Logger.Debug(menu_item)
            if menu_item.itemTypes is None or item.type in menu_item.itemTypes:
                # We don't care for complete here!
                # if menu_item.completeStatus == None or menu_item.completeStatus == item.complete:

                # see if the method is available
                method_available = False

                for method in possible_methods:
                    if method == menu_item.functionName:
                        method_available = True
                        # break from the method loop
                        break

                if not method_available:
                    Logger.warning("No method for: %s", menu_item)
                    continue

                cmd_url = self.parameter_parser.create_action_url(
                    channel, action=menu_item.functionName, item=item)

                cmd = "RunPlugin(%s)" % (cmd_url,)
                title = "Retro: %s" % (menu_item.label,)
                Logger.trace("Adding command: %s | %s", title, cmd)
                context_menu_items.append((title, cmd))

        return context_menu_items

    @staticmethod
    def __get_members(channel):
        """ Caches the inspect.getmembers(channel) or dir(channel) method for performance
        matters.

        :param Channel channel:     The channel from which to get the context menu items.
                                    The channel might be None in case of some actions that
                                    do not require a channel.

        :return: A list of all methods in the channel.
        :rtype: list[str]

        """

        if channel.guid not in AddonAction.__methodContainer:
            # Not working on all platforms
            # self.methodContainer[channel.guid] = inspect.getmembers(channel)
            AddonAction.__methodContainer[channel.guid] = dir(channel)

        return AddonAction.__methodContainer[channel.guid]
