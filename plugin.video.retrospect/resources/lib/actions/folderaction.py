# SPDX-License-Identifier: GPL-3.0-or-later

import xbmcplugin

from resources.lib.actions import action
from resources.lib import contenttype
from resources.lib import mediatype
from resources.lib.actions.addonaction import AddonAction
from resources.lib.addonsettings import AddonSettings
from resources.lib.chn_class import Channel
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.stopwatch import StopWatch
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem
from resources.lib.actions.actionparser import ActionParser
from resources.lib.retroconfig import Config
from resources.lib.textures import TextureHandler
from resources.lib.xbmcwrapper import XbmcWrapper


class FolderAction(AddonAction):
    def __init__(self, parameter_parser, channel, favorites=None):
        """Wraps the channel.process_folder_list

        :param ActionParser parameter_parser:      A ActionParser object to is used to parse and
                                                    create urls
        :param Channel channel:                    The channel info for the channel
        :param list[MediaItem]|None favorites:     Possible list of existing favourites to show

        """

        super(FolderAction, self).__init__(parameter_parser)

        if channel is None and favorites is None:
            raise ValueError("No Channel specified for folder to list")

        self.__channel = channel
        self.__media_item = parameter_parser.media_item
        self.__favorites = favorites

    def execute(self):
        Logger.info("Plugin::process_folder_list Doing process_folder_list")
        try:
            ok = True

            # read the item from the parameters
            selected_item = self.__media_item

            # determine the parent guid
            parent_guid = self.parameter_parser.get_parent_guid(self.__channel, selected_item)

            if self.__favorites is None:
                watcher = StopWatch("Plugin process_folder_list", Logger.instance())
                media_items = self.__channel.process_folder_list(selected_item)
                watcher.lap("Class process_folder_list finished")
            else:
                parent_guid = "{}.fav".format(parent_guid)
                watcher = StopWatch("Plugin process_folder_list With Items", Logger.instance())
                media_items = self.__favorites

            if len(media_items) == 0:
                Logger.warning("process_folder_list returned %s items", len(media_items))
                ok = self.__show_empty_information(media_items, favs=self.__favorites is not None)
            else:
                Logger.debug("process_folder_list returned %s items", len(media_items))

            kodi_items = []

            use_thumbs_as_fanart = AddonSettings.use_thumbs_as_fanart()

            # Determine the TV Show title. Use the TV Show title of the selected item if it has one,
            # or use the title of the selected item if the content has `episodes`. Becaue in that
            # case the selected item is a TV Show.
            tv_show_title = None
            if selected_item:
                tv_show_title = selected_item.tv_show_title or (
                    selected_item.title if selected_item.content_type == contenttype.EPISODES else None
                )

            for media_item in media_items:  # type: MediaItem
                self.__update_artwork(media_item, self.__channel, use_thumbs_as_fanart)
                # Set the TV Show title if it was set before, but don't override existing values.
                if tv_show_title and not media_item.tv_show_title:
                    Logger.trace("Updating TV Show title to: %s", tv_show_title)
                    media_item.tv_show_title = tv_show_title

                if media_item.is_folder:
                    action_value = action.LIST_FOLDER
                    folder = True
                elif media_item.is_playable:
                    action_value = action.PLAY_VIDEO
                    folder = False
                else:
                    Logger.critical("Plugin::process_folder_list: Cannot determine what to add")
                    continue

                # Get the Kodi item
                kodi_item = media_item.get_kodi_item()
                self.__set_kodi_properties(kodi_item, media_item, folder,
                                           is_favourite=self.__favorites is not None)

                # Get the context menu items
                context_menu_items = self._get_context_menu_items(self.__channel, item=media_item, store_id=parent_guid)
                kodi_item.addContextMenuItems(context_menu_items)

                # Get the action URL
                url = media_item.actionUrl
                if url is None:
                    url = self.parameter_parser.create_action_url(
                        self.__channel, action=action_value, item=media_item, store_id=parent_guid)

                # Add them to the list of Kodi items
                kodi_items.append((url, kodi_item, folder))

            watcher.lap("Kodi Items generated")

            # add items but if OK was False, keep it like that
            ok = ok and xbmcplugin.addDirectoryItems(self.handle, kodi_items, len(kodi_items))
            watcher.lap("items send to Kodi")

            if ok and parent_guid is not None:
                self.parameter_parser.pickler.store_media_items(parent_guid, selected_item, media_items)

            watcher.stop()

            self.__add_sort_method_to_handle(self.handle, media_items)
            self.__add_breadcrumb(self.handle, self.__channel, selected_item)
            self.__add_content_type(self.handle, self.__channel, selected_item)

            xbmcplugin.endOfDirectory(self.handle, ok)
        except Exception:
            Logger.error("Plugin::Error Processing FolderList", exc_info=True)
            XbmcWrapper.show_notification(
                LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                LanguageHelper.get_localized_string(LanguageHelper.ErrorList),
                XbmcWrapper.Error, 4000)
            xbmcplugin.endOfDirectory(self.handle, False)

    def __show_empty_information(self, items, favs=False):
        """ Adds an empty item to a list or just shows a message.
        @type favs: boolean
        @param items:

        :param list[MediaItem] items:   The list of items.
        :param bool favs:               Indicating that we are dealing with favourites.

        :return: boolean indicating to report the listing as succes or not.
        :rtype: ok

        """

        if favs:
            title = LanguageHelper.get_localized_string(LanguageHelper.NoFavsId)
        else:
            title = LanguageHelper.get_localized_string(LanguageHelper.ErrorNoEpisodes)

        behaviour = AddonSettings.get_empty_list_behaviour()

        Logger.debug("Showing empty info for mode (favs=%s): [%s]", favs, behaviour)
        if behaviour == "error":
            # show error
            ok = False
        elif behaviour == "dummy" and not favs:
            # We should add a dummy items, but not for favs
            empty_list_item = MediaItem("- %s -" % (title.strip("."), ), "", mediatype.VIDEO)
            empty_list_item.dontGroup = True
            empty_list_item.complete = True

            # if we add one, set OK to True
            ok = True
            items.append(empty_list_item)
        else:
            ok = True

        XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                      title, XbmcWrapper.Error, 2500)
        return ok

    def __update_artwork(self, media_item, channel, use_thumbs_as_fanart):
        """ Updates the fanart and icon of a MediaItem if thoses are missing.

        :param MediaItem media_item:        The item to update
        :param Channel channel:             A possible selected channel
        :param bool use_thumbs_as_fanart:   Use thumbs for artwork

        """

        if media_item is None:
            return

        if channel:
            # take the channel values
            fallback_icon = channel.icon
            fallback_thumb = channel.noImage
            fallback_fanart = channel.fanart
            fallback_poster = channel.poster
            parent_item = channel.parentItem
        else:
            # else the Retrospect ones
            fallback_icon = Config.icon
            fallback_thumb = Config.fanart
            fallback_fanart = Config.fanart
            fallback_poster = None
            parent_item = None

        if parent_item is not None:
            fallback_icon = parent_item.icon or fallback_icon
            fallback_thumb = parent_item.thumb or fallback_thumb
            fallback_fanart = parent_item.fanart or fallback_fanart
            fallback_poster = parent_item.poster or fallback_poster

        # keep it or use the fallback
        if not media_item.is_playable and not media_item.poster and not media_item.thumb:
            # Only set a fallback poster on none-playable items that do not have a poster and
            # don't have a thumb. Otherwise Kodi will always display the fallback poster. The
            # thumb is preferred in that case.
            media_item.poster = fallback_poster
        media_item.icon = media_item.icon or fallback_icon
        media_item.thumb = media_item.thumb or fallback_thumb
        media_item.fanart = media_item.fanart or fallback_fanart

        if use_thumbs_as_fanart and \
                TextureHandler.instance().is_texture_or_empty(media_item.fanart) and \
                not TextureHandler.instance().is_texture_or_empty(media_item.thumb):
            media_item.fanart = media_item.thumb

        return

    def __set_kodi_properties(self, kodi_item, media_item, is_folder, is_favourite):
        """ Sets any Kodi related properties.

        :param xbmcgui.ListItem kodi_item:  The Kodi list item.
        :param MediaItem media_item:        The internal media item.
        :param bool is_folder:              Is this a folder.
        :param bool is_favourite:           Is this a favourite.

        """

        # Set the properties for the context menu add-on
        kodi_item.setProperty(self._propertyRetrospect, "true")
        kodi_item.setProperty(self._propertyRetrospectFolder
                              if is_folder
                              else self._propertyRetrospectVideo, "true")

        if is_favourite:
            kodi_item.setProperty(self._propertyRetrospectFavorite, "true")
        elif media_item.isCloaked:
            kodi_item.setProperty(self._propertyRetrospectCloaked, "true")

        if self.__channel and self.__channel.adaptiveAddonSelectable:
            kodi_item.setProperty(self._propertyRetrospectAdaptive, "true")

        if self.__channel and self.__channel.hasSettings:
            kodi_item.setProperty(self._propertyRetrospectChannelSetting, "true")

    def __add_sort_method_to_handle(self, handle, items=None):
        """ Add a sort method to the plugin output. It takes the Add-On settings into
        account. But if none of the items have a date, it is forced to sort by name.

        :param int handle:              The handle to add the sortmethod to.
        :param list[MediaItem] items:   The items that need to be sorted

        :rtype: None

        """

        sort_methods = []

        # Add the default sorting options
        if AddonSettings.mix_folders_and_videos():
            sort_methods.append(xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        else:
            sort_methods.append(xbmcplugin.SORT_METHOD_LABEL)  # 1
        sort_methods.append(xbmcplugin.SORT_METHOD_UNSORTED)   # 40

        # And then the specialized ones ad default sort options
        if items:
            has_dates = any([i.has_date() for i in items])
            if has_dates:
                sort_methods.insert(0, xbmcplugin.SORT_METHOD_DATE)  # 3

            has_tracks = any([i.has_track() for i in items])
            if has_tracks:
                sort_methods.insert(0, xbmcplugin.SORT_METHOD_TRACKNUM)

            # Check for episodes
            if all([(i.has_info_label(MediaItem.LabelEpisode) and i.is_playable) for i in items]):
                # All playable items have episodes, pre-sort them on that.
                sort_methods.insert(0, xbmcplugin.SORT_METHOD_EPISODE)  # 24

            elif any([i.has_info_label(MediaItem.LabelEpisode) for i in items]):
                # Some items have episodes, only add the sorting options.
                sort_methods.append(xbmcplugin.SORT_METHOD_EPISODE)  # 24

        # Actually add them
        Logger.debug("Sorting methods: %s", sort_methods)
        for sort_method in sort_methods:
            xbmcplugin.addSortMethod(handle=handle, sortMethod=sort_method)
        return

    # noinspection PyUnusedLocal
    def __add_breadcrumb(self, handle, channel, selected_item, last_only=False):
        """ Updates the Kodi category with a breadcrumb to the current parent item

        :param int handle:                      The Kodi file handle
        :param ChannelInfo|Channel channel:     The channel to which the item belongs
        :param MediaItem selected_item:         The item from which to show the breadcrumbs
        :param bool last_only:                  Show only the last item

        """

        bread_crumb = None
        if selected_item is not None:
            if selected_item.tv_show_title and selected_item.tv_show_title != selected_item.name:
                bread_crumb = "{} / {}".format(selected_item.tv_show_title, selected_item.name)
            else:
                bread_crumb = selected_item.name
        elif self.__channel is not None:
            bread_crumb = channel.channelName

        if not bread_crumb:
            return

        bread_crumb = HtmlEntityHelper.convert_html_entities(bread_crumb)
        xbmcplugin.setPluginCategory(handle=handle, category=bread_crumb)

    def __add_content_type(self, handle, channel, selected_item):
        """ Updates the Kodi category with a breadcrumb to the current parent item

        :param int handle:                      The Kodi file handle
        :param ChannelInfo|Channel channel:     The channel to which the item belongs
        :param MediaItem selected_item:         The item from which to show the breadcrumbs

        """

        # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos,
        # videos, images, games (see https://romanvm.github.io/Kodistubs/_autosummary/xbmcplugin.html)
        # set the content. It needs to be "episodes" to make the MediaItem.set_season_info() work
        if selected_item:
            content_type = selected_item.content_type
        elif channel:
            content_type = channel.mainListContentType
        else:
            content_type = contenttype.EPISODES

        if content_type not in contenttype.ALL:
            raise ValueError("Invalid content type: {}".format(content_type))

        Logger.debug("Setting content-type to: %s", content_type)
        if content_type is not None:
            xbmcplugin.setContent(handle=handle, content=content_type)
        else:
            Logger.debug("Not setting content-type")
