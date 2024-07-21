# SPDX-License-Identifier: GPL-3.0-or-later
import re
from typing import Optional, List

import xbmc
import xbmcplugin

from resources.lib import contenttype
from resources.lib.actions import action, keyword
from resources.lib.actions.actionparser import ActionParser
from resources.lib.actions.addonaction import AddonAction
from resources.lib.actions.folderaction import FolderAction
from resources.lib.addonsettings import AddonSettings, LOCAL
from resources.lib.chn_class import Channel
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.logger import Logger
from resources.lib.mediaitem import FolderItem, MediaItem
from resources.lib.xbmcwrapper import XbmcWrapper


class SearchAction(AddonAction):
    __channel: Channel
    __needle: Optional[str]
    __media_item: MediaItem

    def __init__(self, parameter_parser: ActionParser, channel: Channel, needle: Optional[str]):
        """Wraps the channel.process_folder_list

        :param parameter_parser:      A ActionParser object to is used to parse and create urls
        :param channel:               The channel info for the channel
        :needle:                      The needle

        """

        super().__init__(parameter_parser)

        self.__needle = needle if needle is None else HtmlEntityHelper.url_decode(needle)
        self.__settings = AddonSettings.store(store_location=LOCAL)
        self.__media_item = parameter_parser.media_item
        self.__channel = channel
        Logger.debug(f"Searching for: {self.__needle}")

    def execute(self):
        # read the item from the parameters
        selected_item: MediaItem = self.__media_item

        # determine the parent guid
        parent_guid = self.parameter_parser.get_parent_guid(self.__channel, selected_item)

        if self.__needle is None:
            self.__generate_search_history(selected_item, parent_guid)
            return

        elif not self.__needle:
            # Search input
            needle = XbmcWrapper.show_key_board()
            if not needle:
                xbmcplugin.endOfDirectory(self.handle, False, cacheToDisc=True)
                return

            # noinspection PyTypeChecker
            history: List[str] = self.__settings.get_setting("search", self.__channel, [])  # type: ignore
            history = list(set([needle] + history))
            self.__settings.set_setting("search", history[0:10], self.__channel)

            # Make sure we actually load a new URL so a refresh won't pop up a loading screen.
            needle = HtmlEntityHelper.url_encode(needle)
            xbmcplugin.endOfDirectory(self.handle, True, cacheToDisc=True)
            url = self.parameter_parser.create_action_url(self.__channel, action.SEARCH, needle=needle)
            xbmc.executebuiltin(f"Container.Update({url})")

        else:
            media_items = self.__channel.search_site(needle=self.__needle)
            re_needle = re.escape(self.__needle)
            Logger.debug(f"Highlighting {self.__needle} `{re_needle}` in results.")
            highlighter = re.compile(f"({re_needle})", re.IGNORECASE)

            for item in media_items:
                item.name = highlighter.sub(r"[COLOR gold]\1[/COLOR]", item.name)
                if item.description:
                    item.description = highlighter.sub(r"[COLOR gold]\1[/COLOR]", item.description)
            folder_action = FolderAction(self.parameter_parser, self.__channel, items=media_items)
            folder_action.execute()

    def __generate_search_history(self, selected_item: MediaItem, parent_guid: str):
        # noinspection PyTypeChecker
        history: List[str] = self.__settings.get_setting("search", self.__channel, [])

        media_items = []
        search_item = FolderItem(
            f"\b{LanguageHelper.get_localized_string(LanguageHelper.NewSearch)}",
            f"{self.__channel.search_url}&{keyword.NEEDLE}=",
            content_type=contenttype.VIDEOS
        )
        search_item.actionUrl = search_item.url
        media_items.append(search_item)

        for needle in history:
            encoded_needle = HtmlEntityHelper.url_encode(needle)
            url = self.parameter_parser.create_action_url(self.__channel, action.SEARCH,
                                                          needle=encoded_needle)
            item = FolderItem(needle, url, content_type=contenttype.VIDEOS)
            item.actionUrl = url
            item.metaData["retrospect:needle"] = needle
            media_items.append(item)

        folder_action = FolderAction(self.parameter_parser, self.__channel, items=media_items)
        folder_action.execute()
