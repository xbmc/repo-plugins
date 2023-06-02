# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import envcontroller
from resources.lib.logger import Logger
from resources.lib.addonsettings import AddonSettings
from resources.lib.retroconfig import Config
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.channelimporter import ChannelIndex
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.helpers.sessionhelper import SessionHelper
from resources.lib.actions.actionparser import ActionParser
from resources.lib.actions import keyword
from resources.lib.actions import action


class Plugin(ActionParser):
    """ Main Plugin Class

    This class makes it possible to access all the XOT channels as a Kodi Add-on
    instead of a script.

    """

    def __init__(self, addon_name, params, handle=0):
        """ Initialises the plugin with given arguments.

        :param str addon_name:      The add-on name.
        :param str params:          The input parameters from the query string.
        :param int|str handle:      The Kodi directory handle.

        """

        Logger.info("*********** Starting %s add-on version %s ***********", Config.appName, Config.version)
        # noinspection PyTypeChecker

        super(Plugin, self).__init__(addon_name, handle, params)
        Logger.debug(self)

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

            # empty picklestore
            self.pickler.purge_store(Config.addonId)

        # create a session
        SessionHelper.create_session(Logger.instance())

    def run(self):  # NOSONAR
        addon_action = None
        channel_object = None

        if len(self.params) == 0:
            # Show initial start if not in a session now show the list
            if AddonSettings.show_categories():
                from resources.lib.actions.categoryaction import CategoryAction
                addon_action = CategoryAction(self)
            else:
                from resources.lib.actions.channellistaction import ChannelListAction
                addon_action = ChannelListAction(self)

        else:
            # Determine what action to perform based on the parameters
            if keyword.CHANNEL in self.params:
                # retrieve channel characteristics
                channel_url_id = self.params[keyword.CHANNEL]
                channel_code = self.params[keyword.CHANNEL_CODE]
                Logger.debug("Found Channel data in URL: channel='%s', code='%s'",
                             channel_url_id, channel_code)

                # import the channel
                channel_register = ChannelIndex.get_register()
                channel = channel_register.get_channel(channel_url_id, channel_code)

                if channel is not None:
                    channel_object = channel
                else:
                    Logger.critical("None or more than one channels were found, unable to continue.")
                    return

                # init the channel as plugin
                channel_object.init_channel()
                Logger.info("Loaded: %s", channel_object.channelName)

            #===============================================================================
            # See what needs to be done.
            #===============================================================================
            # From here we need the "action" keyword to be present
            if keyword.ACTION not in self.params:
                Logger.critical("Action parameters missing from request. Parameters=%s", self.params)
                return

            if self.params[keyword.ACTION] in \
                    (action.SET_ENCRYPTED_VALUE, action.SET_ENCRYPTION_PIN, action.RESET_VAULT):
                action_value = self.params[keyword.ACTION]
                from resources.lib.actions.vaultaction import VaultAction
                addon_action = VaultAction(self, action_value)

            elif self.params[keyword.ACTION] == action.POST_LOG:
                from resources.lib.actions.logaction import LogAction
                addon_action = LogAction(self)

            elif self.params[keyword.ACTION] == action.CLEANUP:
                from resources.lib.actions.cleanaction import CleanAction
                addon_action = CleanAction(self)

            elif self.params[keyword.ACTION] == action.LIST_CATEGORY:
                from resources.lib.actions.channellistaction import ChannelListAction
                addon_action = ChannelListAction(self, self.params[keyword.CATEGORY])

            elif self.params[keyword.ACTION] == action.CONFIGURE_CHANNEL:
                from resources.lib.actions.configurechannelaction import ConfigureChannelAction
                addon_action = ConfigureChannelAction(self, channel_object)

            elif self.params[keyword.ACTION] == action.CHANNEL_FAVOURITES:
                # we should show the favourites
                from resources.lib.actions.favouritesaction import ShowFavouritesAction
                addon_action = ShowFavouritesAction(self, channel_object)

            elif self.params[keyword.ACTION] == action.ALL_FAVOURITES:
                from resources.lib.actions.favouritesaction import ShowFavouritesAction
                addon_action = ShowFavouritesAction(self, None)

            elif self.params[keyword.ACTION] == action.OPEN_SHORTCUT:
                from resources.lib.actions.shortcutaction import OpenShortcutAction
                addon_action = OpenShortcutAction(self)

            elif self.params[keyword.ACTION] == action.LIST_FOLDER:
                # channelName and U.lib.aRL is present, Parse the folder
                from resources.lib.actions.folderaction import FolderAction
                addon_action = FolderAction(self, channel_object)

            elif self.params[keyword.ACTION] == action.PLAY_VIDEO:
                from resources.lib.actions.videoaction import VideoAction
                addon_action = VideoAction(self, channel_object)

            elif self.params[keyword.ACTION] == action.IPTVMANAGER:
                from resources.lib.actions.iptvmanageraction import IPTVManagerAction
                addon_action = IPTVManagerAction(self, self.params[keyword.REQUEST], int(self.params[keyword.PORT]))

            elif not self.params[keyword.ACTION] == "":
                from resources.lib.actions.contextaction import ContextMenuAction
                addon_action = ContextMenuAction(
                    self, channel_object, self.params[keyword.ACTION])

            else:
                Logger.warning("Number of parameters (%s) or parameter (%s) values not implemented",
                               len(self.params), self.params)

        # Execute the action
        if addon_action is not None:
            addon_action.execute()

        return
