# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import sys
import os
import datetime
import time

from resources.lib.backtothefuture import PY3
if PY3:
    import glob

from resources.lib.addonsettings import AddonSettings
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.retroconfig import Config
from resources.lib.channelinfo import ChannelInfo
from resources.lib.logger import Logger
from resources.lib.textures import TextureHandler
from resources.lib.helpers.stopwatch import StopWatch
from resources.lib.chn_class import Channel


class ChannelIndex(object):
    """ Class that handles the deploying and loading of available channels."""

    __channelIndexer = None  # : Property to store the channel indexer in.

    @staticmethod
    def get_register():
        """ Returns the current active channel register. """

        valid_for = datetime.timedelta(minutes=1)
        # In Kodi Leia the Python instance is not killed and the ChannelRegister stays alive.
        # This might cause some issues. So better to let it expire after some time. But to make it
        # not happen during a user's browsing session, we use sliding expiration of 1 minute.

        if not ChannelIndex.__channelIndexer:
            Logger.debug("Creating a new ChannelIndex-er.")
            ChannelIndex.__channelIndexer = ChannelIndex()
        elif ChannelIndex.__channelIndexer.validAt + valid_for < datetime.datetime.now():
            Logger.debug("Existing ChannelIndex-er expired. Creating a new ChannelIndex-er.")
            ChannelIndex.__channelIndexer = ChannelIndex()
        else:
            Logger.debug("Using an existing %s.", ChannelIndex.__channelIndexer)
            # We are using a sliding expiration, so we should let the expiration slide.
            ChannelIndex.__channelIndexer.validAt = datetime.datetime.now()

        return ChannelIndex.__channelIndexer

    def __init__(self):
        """ Initialize the importer by reading the channels from the channel
        resource folder and will start the import of the channels

        It also deploys the channels from the retrospect/deploy folder.

        """

        self.__INTERNAL_CHANNEL_PATH = "channels"

        # initialise the collections
        self.__allChannels = []  # list of all available channels, used for deduplications

        self.validAt = datetime.datetime.now()
        self.id = int(time.time())
        return

    def get_channel(self, channel_id, channel_code, info_only=False):
        """ Fetches a single channel for a given className and channelCode

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        :param str|unicode channel_id:      The chn_<name> class name.
        :param str|unicode channel_code:    A possible channel code within the channel set.
        :param bool info_only:              Only return the ChannelInfo.

        :return: a Channel object
        :rtype: Channel

        """

        # determine the channel folder
        channel_path = os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH)
        channel_pack, channel_set = channel_id.rsplit(".", 1)
        channel_set_info_path = os.path.join(channel_path, channel_pack, channel_set, "chn_{}.json".format(channel_set))

        channel_infos = ChannelInfo.from_json(channel_set_info_path)
        if channel_code is None:
            channel_infos = [ci for ci in channel_infos if ci.channelCode is None]
        else:
            channel_infos = [ci for ci in channel_infos if ci.channelCode == channel_code]

        if len(channel_infos) != 1:
            Logger.error("Found none or more than 1 matches for '%s' and '%s' in the channel index.",
                         channel_id, channel_code or "None")
            return None
        else:
            Logger.debug("Found single channel in the channel index: %s.", channel_infos[0])

        channel_info = channel_infos[0]
        if self.__is_channel_set_updated(channel_info):
            Logger.warning("Found updated channel_set: %s.", channel_set_info_path)

            # new we should init all channels by loading them all, just to be sure that all is ok
            Logger.debug("Going to fetching all channels to init them all.")
            self.get_channels()
            return self.get_channel(channel_id, channel_code)

        if channel_info.ignore:
            Logger.warning("Channel %s is ignored in channel set", channel_info)
            return None

        if info_only:
            return channel_info

        return channel_info.get_channel()

    # noinspection PyUnusedLocal
    def get_channels(self, include_disabled=False, **kwargs):  # NOSONAR
        """ Retrieves all enabled channels within Retrospect.

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        :param bool include_disabled:   Boolean to indicate if we should include those channels
                                        that are explicitly disabled from the settings.
        :param dict kwargs:             Here for backward compatibility.

        :return: a list of ChannelInfo objects of enabled channels.
        :rtype: list[ChannelInfo]

        """

        sw = StopWatch("ChannelIndex.get_channels Importer", Logger.instance())
        Logger.info("Fetching all enabled channels.")

        self.__allChannels = []
        valid_channels = []

        channels_updated = False
        country_visibility = {}

        channel_path = os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH)
        for channel_pack in os.listdir(channel_path):
            if not channel_pack.startswith("channel."):
                continue

            for channel_set in os.listdir(os.path.join(channel_path, channel_pack)):
                channel_set_path = os.path.join(channel_path, channel_pack, channel_set)
                if not os.path.isdir(channel_set_path):
                    continue

                channel_set_info_path = os.path.join(channel_set_path, "chn_{}.json".format(channel_set))
                channel_infos = ChannelInfo.from_json(channel_set_info_path)

                # Check if the channel was updated
                if self.__is_channel_set_updated(channel_infos[0]):
                    if not channels_updated:
                        # this was the first update found (otherwise channelsUpdated was True) show a message:
                        title = LanguageHelper.get_localized_string(LanguageHelper.InitChannelTitle)
                        text = LanguageHelper.get_localized_string(LanguageHelper.InitChannelText)
                        XbmcWrapper.show_notification(title, text, display_time=15000, logger=Logger.instance())
                    channels_updated |= True

                    # Initialise the channelset.
                    self.__initialise_channel_set(channel_infos[0])

                    # And perform all first actions for the included channels in the set
                    for channel_info in channel_infos:
                        self.__initialise_channel(channel_info)

                # Check the channel validity
                for channel_info in channel_infos:
                    if not self.__channel_is_correct(channel_info):
                        continue
                    self.__allChannels.append(channel_info)

                    if channel_info.ignore:
                        Logger.warning("Not loading: %s -> ignored in the channel set", channel_info)
                        continue
                    valid_channels.append(channel_info)

                    # was the channel hidden based on language settings? We do some caching to speed
                    # things up.
                    if channel_info.language not in country_visibility:
                        country_visibility[channel_info.language] = AddonSettings.show_channel_with_language(channel_info.language)
                    channel_info.visible = country_visibility[channel_info.language]

                    # was the channel explicitly disabled from the settings?
                    channel_info.enabled = AddonSettings.get_channel_visibility(channel_info)

                    Logger.debug("Found channel: %s", channel_info)

        if channels_updated:
            Logger.info("New or updated channels found. Updating add-on configuration for all channels and user agent.")
            AddonSettings.update_add_on_settings_with_channels(valid_channels, Config)
            AddonSettings.update_user_agent()
        else:
            Logger.debug("No channel changes found. Skipping add-on configuration for channels.")
            # TODO: perhaps we should check that the settings.xml is correct and not broken?

        valid_channels.sort(key=lambda c: c.sort_key)
        visible_channels = [ci for ci in valid_channels if ci.visible and ci.enabled]
        Logger.info("Fetch a total of %d channels of which %d are visible.",
                    len(valid_channels),
                    len(visible_channels))

        sw.stop()

        if include_disabled:
            return valid_channels

        return visible_channels

    def get_categories(self):
        # type: () -> set
        """ Retrieves the available categories from the channels. This list is dynamically generated
        based on the active channels.

        :return: A list of available categories for the channels.
        :rtype: list[str|unicode]

        """

        categories = set()
        channels = self.get_channels()
        list([categories.add(c.category) for c in channels])
        Logger.debug("Found these categories: %s", ", ".join(categories))
        return categories

    def __is_channel_set_updated(self, channel_info):
        """ Checks whether a channel set was updated.

        :param ChannelInfo channel_info: the channelInfo for a channel from the set

        :return: indicating if the channel was updated or not.
        :rtype : bool

        """

        compiled_name = "%s.pyc" % (channel_info.moduleName,)
        optimized_name = "%s.pyo" % (channel_info.moduleName,)

        # A channel set is updated if no Optimized (.pyo) and no Compiled (.pyc) files are
        # there.
        if os.path.isfile(os.path.join(channel_info.path, compiled_name)) or \
                os.path.isfile(os.path.join(channel_info.path, optimized_name)):
            return False

        # If we run Python 3 and no files are in the Python3 __pycache__ folders a channel is
        # also considered updated.
        if PY3 and glob.glob(os.path.join(channel_info.path, "__pycache__", "*.py*")):
            return False

        return True

    def __channel_is_correct(self, channel_info):
        # type: (ChannelInfo) -> bool
        """ Validates if the given channel with channelInfo is correct

        @param channel_info: The channelInfo to use to validate the channel
        @return:            True/False if valid or not.

        """

        if not channel_info.guid:
            Logger.error("Not loading: %s -> No guid present.", channel_info)
            return False

        if channel_info in self.__allChannels:
            existing_channel = self.__allChannels[self.__allChannels.index(channel_info)]
            Logger.error("Not loading: %s -> a channel with the same guid already exist:\n%s.",
                         channel_info, existing_channel)
            return False

        return True

    def __initialise_channel_set(self, channel_info):
        # type: (ChannelInfo) -> None
        """ Initialises a channelset (.py file)

        WARNING: these actions are done ONCE per python file, not per channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo

        Keyword Arguments:
        abortOnNew  : Boolean - If set to true, channel initialisation will not continue if a new channel was found.
                                This will have to be done later.

        Returns True if any operations where executed

        """

        Logger.info("Initialising channel set at: %s.", channel_info.path)

        # now import (required for the PerformFirstTimeActions
        sys.path.append(channel_info.path)

        # make sure a pyo or pyc exists
        # __import__(channelInfo.moduleName)
        # The debugger won't compile if __import__ is used. So let's use this one.
        import py_compile
        py_compile.compile(os.path.join(channel_info.path, "%s.py" % (channel_info.moduleName,)))

        # purge the texture cache.
        if TextureHandler.instance():
            TextureHandler.instance().purge_texture_cache(channel_info)
        else:
            Logger.warning("Could not purge_texture_cache: no TextureHandler available")
        return

    def __initialise_channel(self, channel_info):
        # type: (ChannelInfo) -> None
        """ Performs the first time channel actions for a given channel.

        Arguments:
        channelInfo : ChannelInfo - The channelinfo
        """

        Logger.info("Performing first time channel actions for: %s.", channel_info)

        self.__show_first_time_message(channel_info)
        return

    def __show_first_time_message(self, channel_info):
        """ Checks if it is the first time a channel is executed and if a first time message is
        available it will be shown.

        Shows a message dialog if the message should be shown.  Make sure that each line fits
        in a single line of a Kodi Dialog box (50 chars).

        :param ChannelInfo channel_info:    The ChannelInfo to show a message for.

        """

        hide_first_time = AddonSettings.hide_first_time_messages()
        if channel_info.firstTimeMessage:
            if not hide_first_time:
                Logger.info("Showing first time message '%s' for channel chn_%s.",
                            channel_info.firstTimeMessage, channel_info.moduleName)

                title = LanguageHelper.get_localized_string(LanguageHelper.ChannelMessageId)
                XbmcWrapper.show_dialog(title, channel_info.firstTimeMessage)
            else:
                Logger.debug("Not showing first time message due to add-on setting set to '%s'.",
                             hide_first_time)
        return

    def __str__(self):
        """ String representation of the object.

        :return: String representation of the object.
        :type: str|unicode

        """

        return "ChannelIndex for {} (id={})".format(Config.profileDir, self.id)
