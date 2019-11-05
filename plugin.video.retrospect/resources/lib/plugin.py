# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import xbmcplugin
import xbmc
import xbmcgui

from resources.lib import envcontroller
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings
from resources.lib.locker import LockWithDialog
from resources.lib.retroconfig import Config
from resources.lib.xbmcwrapper import XbmcWrapper, XbmcDialogProgressWrapper, XbmcDialogProgressBgWrapper
from resources.lib.mediaitem import MediaItem
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.stopwatch import StopWatch
from resources.lib.helpers.sessionhelper import SessionHelper
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.textures import TextureHandler
from resources.lib.paramparser import ParameterParser
from resources.lib.channelinfo import ChannelInfo
from resources.lib.chn_class import Channel


class Plugin(ParameterParser):
    """ Main Plugin Class

    This class makes it possible to access all the XOT channels as a Kodi Add-on
    instead of a script.

    """

    def __init__(self, addon_name, params, handle=0):  # NOSONAR complexity
        """ Initialises the plugin with given arguments.

        :param str addon_name:      The add-on name.
        :param str params:          The input parameters from the query string.
        :param int handle:          The Kodi directory handle.

        """

        Logger.info("*********** Starting %s add-on version %s ***********", Config.appName, Config.version)
        # noinspection PyTypeChecker
        self.handle = int(handle)

        super(Plugin, self).__init__(addon_name, params)
        Logger.debug("Plugin Params: %s (%s)\n"
                     "Handle:      %s\n"
                     "Name:        %s\n"
                     "Query:       %s", self.params, len(self.params),
                     self.handle, self.pluginName, params)

        # channel objects
        self.channelObject = None
        self.channelFile = ""
        self.channelCode = None

        self.contentType = "episodes"
        self.methodContainer = dict()   # : storage for the inspect.getmembers(channel) method. Improves performance

        # are we in session?
        session_active = SessionHelper.is_session_active(Logger.instance())

        # fetch some environment settings
        env_ctrl = envcontroller.EnvController(Logger.instance())

        if not session_active:
            # do add-on start stuff
            Logger.info("Add-On start detected. Performing startup actions.")

            # print the folder structure
            env_ctrl.print_retrospect_settings_and_folders(Config, AddonSettings)

            # show notification
            XbmcWrapper.show_notification(None, LanguageHelper.get_localized_string(LanguageHelper.StartingAddonId) % (
                Config.appName,), fallback=False, logger=Logger)

            # check for cache folder
            env_ctrl.cache_check()

            # do some cache cleanup
            env_ctrl.cache_clean_up(Config.cacheDir, Config.cacheValidTime)

        # create a session
        SessionHelper.create_session(Logger.instance())

        #===============================================================================
        #        Start the plugin version of progwindow
        #===============================================================================
        if len(self.params) == 0:

            # Show initial start if not in a session
            # now show the list
            if AddonSettings.show_categories():
                self.show_categories()
            else:
                self.show_channel_list()

        #===============================================================================
        #        Start the plugin verion of the episode window
        #===============================================================================
        else:
            # Determine what stage we are in. Check that there are more than 2 Parameters
            if len(self.params) > 1 and self.keywordChannel in self.params:
                # retrieve channel characteristics
                self.channelFile = os.path.splitext(self.params[self.keywordChannel])[0]
                self.channelCode = self.params[self.keywordChannelCode]
                Logger.debug("Found Channel data in URL: channel='%s', code='%s'", self.channelFile,
                             self.channelCode)

                # import the channel
                channel_register = ChannelIndex.get_register()
                channel = channel_register.get_channel(self.channelFile, self.channelCode)

                if channel is not None:
                    self.channelObject = channel
                else:
                    Logger.critical("None or more than one channels were found, unable to continue.")
                    return

                # init the channel as plugin
                self.channelObject.init_channel()
                Logger.info("Loaded: %s", self.channelObject.channelName)

            elif self.keywordCategory in self.params \
                    or self.keywordAction in self.params and (
                        self.params[self.keywordAction] == self.actionAllFavourites or
                        self.params[self.keywordAction] == self.actionRemoveFavourite):
                # no channel needed for these favourites actions.
                pass

            # ===============================================================================
            # Vault Actions
            # ===============================================================================
            elif self.keywordAction in self.params and \
                    self.params[self.keywordAction] in \
                    (
                        self.actionSetEncryptedValue,
                        self.actionSetEncryptionPin,
                        self.actionResetVault
                    ):
                try:
                    # Import vault here, as it is only used here or in a channel
                    # that supports it
                    from resources.lib.vault import Vault

                    action = self.params[self.keywordAction]
                    if action == self.actionResetVault:
                        Vault.reset()
                        return

                    v = Vault()
                    if action == self.actionSetEncryptionPin:
                        v.change_pin()
                    elif action == self.actionSetEncryptedValue:
                        v.set_setting(self.params[self.keywordSettingId],
                                      self.params.get(self.keywordSettingName, ""),
                                      self.params.get(self.keywordSettingActionId, None))
                finally:
                    if self.keywordSettingTabFocus in self.params:
                        AddonSettings.show_settings(self.params[self.keywordSettingTabFocus],
                                                    self.params.get(
                                                       self.keywordSettingSettingFocus, None))
                return

            elif self.keywordAction in self.params and \
                    self.actionPostLog in self.params[self.keywordAction]:
                self.__send_log()
                return

            elif self.keywordAction in self.params and \
                    self.actionProxy in self.params[self.keywordAction]:

                # do this here to not close the busy dialog on the SetProxy when
                # a confirm box is shown
                title = LanguageHelper.get_localized_string(LanguageHelper.ProxyChangeConfirmTitle)
                content = LanguageHelper.get_localized_string(LanguageHelper.ProxyChangeConfirm)
                if not XbmcWrapper.show_yes_no(title, content):
                    Logger.warning("Stopping proxy update due to user intervention")
                    return

                language = self.params.get(self.keywordLanguage, None)
                proxy_id = self.params.get(self.keywordProxy, None)
                local_ip = self.params.get(self.keywordLocalIP, None)
                self.__set_proxy(language, proxy_id, local_ip)
                return

            else:
                Logger.critical("Error determining Plugin action")
                return

            #===============================================================================
            # See what needs to be done.
            #===============================================================================
            if self.keywordAction not in self.params:
                Logger.critical("Action parameters missing from request. Parameters=%s", self.params)
                return

            elif self.params[self.keywordAction] == self.actionListCategory:
                self.show_channel_list(self.params[self.keywordCategory])

            elif self.params[self.keywordAction] == self.actionConfigureChannel:
                self.__configure_channel(self.channelObject)

            elif self.params[self.keywordAction] == self.actionFavourites:
                # we should show the favourites
                self.show_favourites(self.channelObject)

            elif self.params[self.keywordAction] == self.actionAllFavourites:
                self.show_favourites(None)

            elif self.params[self.keywordAction] == self.actionListFolder:
                # channelName and URL is present, Parse the folder
                self.process_folder_list()

            elif self.params[self.keywordAction] == self.actionPlayVideo:
                self.play_video_item()

            elif not self.params[self.keywordAction] == "":
                self.on_action_from_context_menu(self.params[self.keywordAction])

            else:
                Logger.warning("Number of parameters (%s) or parameter (%s) values not implemented",
                               len(self.params), self.params)

        self.__fetch_textures()
        return

    def show_categories(self):
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
            kodi_item.setProperty(self.propertyRetrospect, "true")
            kodi_item.setProperty(self.propertyRetrospectCategory, "true")

            if not AddonSettings.hide_fanart():
                kodi_item.setArt({'fanart': fanart})

            url = self._create_action_url(None, action=self.actionListCategory, category=category)
            kodi_items.append((url, kodi_item, True))

        # Logger.Trace(kodi_items)
        ok = xbmcplugin.addDirectoryItems(self.handle, kodi_items, len(kodi_items))
        xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(self.handle, ok)
        return ok

    def show_channel_list(self, category=None):
        """ Displays the channels that are currently available in XOT as a directory
        listing.

        :param str category:    The category to show channels for

        """

        if category:
            Logger.info("Plugin::show_channel_list for %s", category)
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
                kodi_item.setProperty(self.propertyRetrospect, "true")
                kodi_item.setProperty(self.propertyRetrospectCategory, "true")

                if not AddonSettings.hide_fanart():
                    kodi_item.setArt({'fanart': fanart})

                url = self._create_action_url(None, action=self.actionAllFavourites)
                xbmc_items.append((url, kodi_item, True))

            for channel in channels:
                if category and channel.category != category:
                    Logger.debug("Skipping %s (%s) due to category filter", channel.channelName, channel.category)
                    continue

                # Get the Kodi item
                item = channel.get_kodi_item()
                item.setProperty(self.propertyRetrospect, "true")
                item.setProperty(self.propertyRetrospectChannel, "true")
                if channel.settings:
                    item.setProperty(self.propertyRetrospectChannelSetting, "true")
                if channel.adaptiveAddonSelectable:
                    item.setProperty(self.propertyRetrospectAdaptive, "true")

                # Get the context menu items
                context_menu_items = self.__get_context_menu_items(channel)
                item.addContextMenuItems(context_menu_items)
                # Get the URL for the item
                url = self._create_action_url(channel, action=self.actionListFolder)

                # Append to the list of Kodi Items
                xbmc_items.append((url, item, True))

            # Add the items
            ok = xbmcplugin.addDirectoryItems(self.handle, xbmc_items, len(xbmc_items))

            # Just let Kodi display the order we give.
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
            xbmcplugin.addSortMethod(handle=self.handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)
            xbmcplugin.endOfDirectory(self.handle, ok)
        except:
            xbmcplugin.endOfDirectory(self.handle, False)
            Logger.critical("Error fetching channels for plugin", exc_info=True)

    def show_favourites(self, channel):
        """ Show the favourites (for a channel).

        :param ChannelInfo|None channel:    The channel to show favourites for.
                                            Might be None to show all.

        """

        Logger.debug("Plugin::show_favourites")

        if channel is None:
            Logger.info("Showing all favourites")
        else:
            Logger.info("Showing favourites for: %s", channel)

        # Local import for performance
        from resources.lib.favourites import Favourites
        f = Favourites(Config.favouriteDir)
        favs = f.list(channel)
        self.process_folder_list(favs)

    def process_folder_list(self, favorites=None):
        """Wraps the channel.process_folder_list

        :param list[MediaItem]|None favorites:

        """

        Logger.info("Plugin::process_folder_list Doing process_folder_list")
        try:
            ok = True

            selected_item = None
            if self.keywordPickle in self.params:
                selected_item = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])

            if favorites is None:
                watcher = StopWatch("Plugin process_folder_list", Logger.instance())
                media_items = self.channelObject.process_folder_list(selected_item)
                watcher.lap("Class process_folder_list finished")
            else:
                watcher = StopWatch("Plugin process_folder_list With Items", Logger.instance())
                media_items = favorites

            if len(media_items) == 0:
                Logger.warning("process_folder_list returned %s items", len(media_items))
                ok = self.__show_empty_information(media_items, favs=favorites is not None)
            else:
                Logger.debug("process_folder_list returned %s items", len(media_items))

            kodi_items = []

            if self.channelObject:
                fallback_icon = self.channelObject.noImage
                fallback_fanart = self.channelObject.fanart
            else:
                fallback_icon = Config.icon
                fallback_fanart = Config.fanart

            for media_item in media_items:  # type: MediaItem
                media_item.thumb = media_item.thumb or fallback_icon
                media_item.fanart = media_item.fanart or fallback_fanart

                if media_item.type == 'folder' or media_item.type == 'append' or media_item.type == "page":
                    action = self.actionListFolder
                    folder = True
                elif media_item.is_playable():
                    action = self.actionPlayVideo
                    folder = False
                else:
                    Logger.critical("Plugin::process_folder_list: Cannot determine what to add")
                    continue

                # Get the Kodi item
                kodi_item = media_item.get_kodi_item()
                self.__set_kodi_properties(kodi_item, media_item, folder,
                                           is_favourite=favorites is not None)

                # Get the context menu items
                context_menu_items = self.__get_context_menu_items(self.channelObject, item=media_item)
                kodi_item.addContextMenuItems(context_menu_items)

                # Get the action URL
                url = media_item.actionUrl
                if url is None:
                    url = self._create_action_url(self.channelObject, action=action, item=media_item)

                # Add them to the list of Kodi items
                kodi_items.append((url, kodi_item, folder))

            watcher.lap("Kodi Items generated")
            # add items but if OK was False, keep it like that
            ok = ok and xbmcplugin.addDirectoryItems(self.handle, kodi_items, len(kodi_items))
            watcher.lap("items send to Kodi")

            if selected_item is None and self.channelObject is not None:
                # mainlist item register channel.
                watcher.lap("Statistics send")

            watcher.stop()

            self.__add_sort_method_to_handle(self.handle, media_items)
            self.__add_breadcrumb(self.handle, self.channelObject, selected_item)

            # set the content
            xbmcplugin.setContent(handle=self.handle, content=self.contentType)

            xbmcplugin.endOfDirectory(self.handle, ok)
        except Exception:
            Logger.error("Plugin::Error Processing FolderList", exc_info=True)
            XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                          LanguageHelper.get_localized_string(LanguageHelper.ErrorList),
                                          XbmcWrapper.Error, 4000)
            xbmcplugin.endOfDirectory(self.handle, False)

    # @LockWithDialog(logger=Logger.instance())  No longer needed as Kodi will do this automatically
    def play_video_item(self):
        """ Starts the videoitem using a playlist. """

        Logger.debug("Playing videoitem using PlayListMethod")

        try:
            media_item = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])

            if not media_item.complete:
                media_item = self.channelObject.process_video_item(media_item)

            # Any warning to show
            self.__show_warnings(media_item)

            # validated the updated media_item
            if not media_item.complete or not media_item.has_media_item_parts():
                Logger.warning("process_video_item returned an MediaItem that had MediaItem.complete = False:\n%s", media_item)

            if not media_item.has_media_item_parts():
                # the update failed or no items where found. Don't play
                XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                              LanguageHelper.get_localized_string(LanguageHelper.NoStreamsId),
                                              XbmcWrapper.Error)
                Logger.warning("Could not start playback due to missing streams. Item:\n%s", media_item)
                xbmcplugin.endOfDirectory(self.handle, False)
                return

            kodi_items = media_item.get_kodi_play_list_data(
                AddonSettings.get_max_stream_bitrate(self.channelObject),
                self.channelObject.proxy
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
            # Get the Kodi Player instance (let Kodi decide what player, see
            # http://forum.kodi.tv/showthread.php?tid=173887&pid=1516662#pid1516662)
            kodi_player = xbmc.Player()
            XbmcWrapper.wait_for_player_to_start(kodi_player, logger=Logger.instance(), url=start_url)

            # TODO: Apparently if we use the InputStream Adaptive, using the setSubtitles() causes sync issues.
            available_subs = [p.Subtitle for p in media_item.MediaItemParts]
            if available_subs:
                kodi_player.setSubtitles(available_subs[0])
            kodi_player.showSubtitles(show_subs)

            xbmcplugin.endOfDirectory(self.handle, True)
        except:
            XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                          LanguageHelper.get_localized_string(LanguageHelper.NoPlaybackId),
                                          XbmcWrapper.Error)
            Logger.critical("Could not playback the url", exc_info=True)

            # We need to single Kodi that it failed and it should not wait longer. Either using a
            # `raise` or with `xbmcplugin.endOfDirectory`. Doing the latter for now although we are
            # not really playing.
            xbmcplugin.endOfDirectory(self.handle, False)

        return

    def on_action_from_context_menu(self, action):
        """Peforms the action from a custom contextmenu

        Arguments:
        action : String - The name of the method to call

        """
        Logger.debug("Performing Custom Contextmenu command: %s", action)

        item = self._pickler.de_pickle_media_item(self.params[self.keywordPickle])
        if not item.complete:
            Logger.debug("The contextmenu action requires a completed item. Updating %s", item)
            item = self.channelObject.process_video_item(item)

            if not item.complete:
                Logger.warning("update_video_item returned an item that had item.complete = False:\n%s", item)

        # invoke
        function_string = "returnItem = self.channelObject.%s(item)" % (action,)
        Logger.debug("Calling '%s'", function_string)
        try:
            # noinspection PyRedundantParentheses
            exec(function_string)  # NOSONAR We just need this here.
        except:
            Logger.error("on_action_from_context_menu :: Cannot execute '%s'.", function_string, exc_info=True)
        return

    def __fetch_textures(self):
        textures_to_retrieve = TextureHandler.instance().number_of_missing_textures()

        if textures_to_retrieve > 0:
            w = None
            try:
                # show a blocking or background progress bar
                if textures_to_retrieve > 4:
                    w = XbmcDialogProgressWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.InitChannelTitle)),
                        LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle),
                        # Config.textureUrl
                    )
                else:
                    w = XbmcDialogProgressBgWrapper(
                        "%s: %s" % (Config.appName, LanguageHelper.get_localized_string(LanguageHelper.FetchTexturesTitle)),
                        Config.textureUrl
                    )

                TextureHandler.instance().fetch_textures(w.progress_update)
            except:
                Logger.error("Error fetching textures", exc_info=True)
            finally:
                if w is not None:
                    # always close the progress bar
                    w.close()
        return

    def __configure_channel(self, channel_info):
        """ Shows the current channels settings dialog.

        :param ChannelInfo channel_info:    The channel info for the channel

        """

        if not channel_info:
            Logger.warning("Cannot configure channel without channel info")

        Logger.info("Configuring channel: %s", channel_info)
        AddonSettings.show_channel_settings(channel_info)

    def __add_sort_method_to_handle(self, handle, items=None):
        """ Add a sort method to the plugin output. It takes the Add-On settings into
        account. But if none of the items have a date, it is forced to sort by name.

        :param int handle:              The handle to add the sortmethod to.
        :param list[MediaItem] items:   The items that need to be sorted

        :rtype: None

        """

        if AddonSettings.mix_folders_and_videos():
            label_sort_method = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS
        else:
            label_sort_method = xbmcplugin.SORT_METHOD_LABEL

        if items:
            has_dates = len(list([i for i in items if i.has_date()])) > 0
            if has_dates:
                Logger.debug("Sorting method: Dates")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=label_sort_method)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

            has_tracks = len(list([i for i in items if i.has_track()])) > 0
            if has_tracks:
                Logger.debug("Sorting method: Tracks")
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=label_sort_method)
                xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
                return

        Logger.debug("Sorting method: Default (Label)")
        xbmcplugin.addSortMethod(handle=handle, sortMethod=label_sort_method)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        return

    def __get_context_menu_items(self, channel, item=None):
        """ Retrieves the custom context menu items to display.

        favouritesList : Boolean   - Indication that the menu is for the favorites

        :param Channel|None channel:    The channel from which to get the context menu items.
                                        The channel might be None in case of some actions that
                                        do not require a channel.
        :param MediaItem|None item:     The item to which the context menu belongs.

        :return: A list of context menu names and their commands.
        :rtype: list[tuple[str,str]]

        """

        context_menu_items = []

        # Genenric, none-Python menu items that would normally cause an unwanted reload of the
        # Python interpreter instance within Kodi.
        refresh = LanguageHelper.get_localized_string(LanguageHelper.RefreshListId)
        context_menu_items.append((refresh, 'XBMC.Container.Refresh()'))

        if item is None:
            return context_menu_items

        # if it was a favourites list, don't add the channel methods as they might be from a different channel
        if channel is None:
            return context_menu_items

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

                cmd_url = self._create_action_url(channel, action=menu_item.functionName, item=item)
                cmd = "XBMC.RunPlugin(%s)" % (cmd_url,)
                title = "Retro: %s" % (menu_item.label,)
                Logger.trace("Adding command: %s | %s", title, cmd)
                context_menu_items.append((title, cmd))

        return context_menu_items

    def __get_members(self, channel):
        """ Caches the inspect.getmembers(channel) or dir(channel) method for performance
        matters.

        :param Channel channel:     The channel from which to get the context menu items.
                                    The channel might be None in case of some actions that
                                    do not require a channel.

        :return: A list of all methods in the channel.
        :rtype: list[str]

        """

        if channel.guid not in self.methodContainer:
            # Not working on all platforms
            # self.methodContainer[channel.guid] = inspect.getmembers(channel)
            self.methodContainer[channel.guid] = dir(channel)

        return self.methodContainer[channel.guid]

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
            empty_list_item = MediaItem("- %s -" % (title.strip("."), ), "", type='video')
            if self.channelObject:
                empty_list_item.icon = self.channelObject.icon
                empty_list_item.thumb = self.channelObject.noImage
                empty_list_item.fanart = self.channelObject.fanart
            else:
                icon = Config.icon
                fanart = Config.fanart
                empty_list_item.icon = icon
                empty_list_item.thumb = fanart
                empty_list_item.fanart = fanart

            empty_list_item.dontGroup = True
            empty_list_item.description = "This listing was left empty intentionally."
            empty_list_item.complete = True
            # add funny stream here?
            # part = empty_list_item.create_new_empty_media_part()
            # for s, b in YouTube.get_streams_from_you_tube("", self.channelObject.proxy):
            #     part.append_media_stream(s, b)

            # if we add one, set OK to True
            ok = True
            items.append(empty_list_item)
        else:
            ok = True

        XbmcWrapper.show_notification(LanguageHelper.get_localized_string(LanguageHelper.ErrorId),
                                      title, XbmcWrapper.Error, 2500)
        return ok

    @LockWithDialog(logger=Logger.instance())
    def __send_log(self):
        """ Send log files via Pastbin or Gist. """

        from resources.lib.helpers.logsender import LogSender
        sender_mode = 'hastebin'
        log_sender = LogSender(Config.logSenderApi, logger=Logger.instance(), mode=sender_mode)
        try:
            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostSuccessTitle)
            url_text = LanguageHelper.get_localized_string(LanguageHelper.LogPostLogUrl)
            files_to_send = [Logger.instance().logFileName, Logger.instance().logFileName.replace(".log", ".old.log")]
            if sender_mode != "gist":
                paste_url = log_sender.send_file(Config.logFileNameAddon, files_to_send[0])
            else:
                paste_url = log_sender.send_files(Config.logFileNameAddon, files_to_send)
            XbmcWrapper.show_dialog(title, url_text % (paste_url,))
        except Exception as e:
            Logger.error("Error sending %s", Config.logFileNameAddon, exc_info=True)

            title = LanguageHelper.get_localized_string(LanguageHelper.LogPostErrorTitle)
            error_text = LanguageHelper.get_localized_string(LanguageHelper.LogPostError)
            error = error_text % (str(e),)
            XbmcWrapper.show_dialog(title, error.strip(": "))

    @LockWithDialog(logger=Logger.instance())
    def __set_proxy(self, language, proxy_id, local_ip):
        """ Sets the proxy and local IP configuration for channels.

        :param str language:    The language for what channels to update.
        :param int proxy_id:    The proxy index to use.
        :param int local_ip:    The local_ip index to use.
        
        If no proxy_id is specified (None) then the proxy_id will be determined based on language
        If no local_ip is specified (None) then the local_ip will be determined based on language
        
        """

        languages = AddonSettings.get_available_countries(as_country_codes=True)

        if language is not None and language not in languages:
            Logger.warning("Missing language: %s", language)
            return

        if proxy_id is None:
            proxy_id = languages.index(language)
        else:
            # noinspection PyTypeChecker
            proxy_id = int(proxy_id)

        if local_ip is None:
            local_ip = languages.index(language)
        else:
            # noinspection PyTypeChecker
            local_ip = int(local_ip)

        channels = ChannelIndex.get_register().get_channels()
        Logger.info("Setting proxy='%s' (%s) and local_ip='%s' (%s) for country '%s'",
                    proxy_id, languages[proxy_id],
                    local_ip, languages[local_ip],
                    language)

        channels_in_country = [c for c in channels if c.language == language or language is None]
        for channel in channels_in_country:
            Logger.debug("Setting Proxy for: %s", channel)
            AddonSettings.set_proxy_id_for_channel(channel, proxy_id)
            if channel.localIPSupported:
                Logger.debug("Setting Local IP for: %s", channel)
                AddonSettings.set_local_ip_for_channel(channel, local_ip)

    def __set_kodi_properties(self, kodi_item, media_item, is_folder, is_favourite):
        """ Sets any Kodi related properties.

        :param xbmcgui.ListItem kodi_item:  The Kodi list item.
        :param MediaItem media_item:        The internal media item.
        :param bool is_folder:              Is this a folder.
        :param bool is_favourite:           Is this a favourite.

        """

        # Set the properties for the context menu add-on
        kodi_item.setProperty(self.propertyRetrospect, "true")
        kodi_item.setProperty(self.propertyRetrospectFolder
                              if is_folder
                              else self.propertyRetrospectVideo, "true")

        if is_favourite:
            kodi_item.setProperty(self.propertyRetrospectFavorite, "true")
        elif media_item.isCloaked:
            kodi_item.setProperty(self.propertyRetrospectCloaked, "true")

        if self.channelObject and self.channelObject.adaptiveAddonSelectable:
            kodi_item.setProperty(self.propertyRetrospectAdaptive, "true")

        if self.channelObject and self.channelObject.hasSettings:
            kodi_item.setProperty(self.propertyRetrospectChannelSetting, "true")

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
            bread_crumb = selected_item.name
        elif self.channelObject is not None:
            bread_crumb = channel.channelName

        if not bread_crumb:
            return

        bread_crumb = HtmlEntityHelper.convert_html_entities(bread_crumb)
        xbmcplugin.setPluginCategory(handle=handle, category=bread_crumb)

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
            play_list.add(current_play_list_items[i].getfilename(), current_play_list_items[i])

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
            play_list.add(current_play_list_items[i].getfilename(), current_play_list_items[i])

        return start_url
