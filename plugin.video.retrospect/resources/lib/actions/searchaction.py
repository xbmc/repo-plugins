# SPDX-License-Identifier: GPL-3.0-or-later
import re
from typing import Optional, List

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
        self.__search_key = self.__get_search_key()
        Logger.debug(f"Searching for: {self.__needle}")

    def __get_search_key(self) -> str:
        """Return the settings key for search history.

        When the channel provides a ``search_profile_id``, the key is scoped
        to that profile so each profile has its own search history.
        The active key is persisted so that Menu operations (clear, remove)
        can find it without instantiating the full channel.
        """
        profile_id = self.__channel.search_profile_id
        if profile_id:
            key = f"search:{profile_id}"
        else:
            key = "search"
        self.__settings.set_setting("search:active_key", key, self.__channel)
        return key

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
            history: List[str] = self.__settings.get_setting(self.__search_key, self.__channel, [])  # type: ignore
            history = [needle] + history
            # de-duplicate without changing order:
            seen = set()
            history = [h for h in history if h not in seen and not seen.add(h)]

            self.__settings.set_setting(self.__search_key, history[0:10], self.__channel)

            # Bug: empty needle is passed through, so a refresh triggers
            # the keyboard pop-up instead of re-running the query.
            media_items = self.__channel.search_site(needle=needle)
            folder_action = FolderAction(self.parameter_parser, self.__channel, items=media_items)
            folder_action.execute()

        else:
            media_items = self.__channel.search_site(needle=self.__needle)
            folder_action = FolderAction(self.parameter_parser, self.__channel, items=media_items)
            folder_action.execute()

    def __generate_search_history(self, selected_item: MediaItem, parent_guid: str):
        # noinspection PyTypeChecker
        history: List[str] = self.__settings.get_setting(self.__search_key, self.__channel, [])

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
