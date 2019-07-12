# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import sys
import os
import io
import shutil
import datetime
import time

from backtothefuture import PY3
if PY3:
    import glob

import envcontroller
from addonsettings import AddonSettings
from regexer import Regexer
from environments import Environments
from xbmcwrapper import XbmcWrapper
from helpers.languagehelper import LanguageHelper
from retroconfig import Config
from channelinfo import ChannelInfo
from logger import Logger
from helpers.jsonhelper import JsonHelper
from textures import TextureHandler
from version import Version
from .stopwatch import StopWatch
from chn_class import Channel


class ChannelIndex(object):
    """ Class that handles the deploying and loading of available channels."""

    __channelIndexer = None  # : Property to store the channel indexer in.

    @staticmethod
    def get_register():
        """ Returns the current active channel register.

        Used for backward compatibility with Xbox.

        """

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
        self.__CHANNEL_INDEX_CHANNEL_KEY = "channels"
        self.__CHANNEL_INDEX_ADD_ONS_KEY = "add-ons"
        self.__CHANNEL_INDEX_CHANNEL_INFO_KEY = "info"
        self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY = "version"
        self.__CHANNEL_INDEX = os.path.join(Config.profileDir, "channelindex.json")

        # initialise the collections
        self.__allChannels = []  # list of all available channels

        self.__reindexed = False
        self.__reindex = self.__deploy_new_channels()
        self.__channelIndex = self.__get_index()

        self.validAt = datetime.datetime.now()
        self.id = int(time.time())
        return

    def get_channel(self, class_name, channel_code, info_only=False):
        """ Fetches a single channel for a given className and channelCode

        If updated channels are found, the those channels are indexed and the
        channel index is rebuild.

        :param str|unicode class_name:      The chn_<name> class name.
        :param str|unicode channel_code:    A possible channel code within the channel set.
        :param bool info_only:              Only return the ChannelInfo.

        :return: a Channel object
        :rtype: Channel

        """

        channel_set = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY].get(class_name, None)
        if channel_set is None:
            Logger.error("Could not find info for channelClass '%s'.", class_name)
            return None

        channel_set_info_path = channel_set[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
        channel_set_version = channel_set[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        if not os.path.isfile(channel_set_info_path) and not self.__reindexed:
            Logger.warning("Missing channel_set file: %s.", channel_set_info_path)
            self.__rebuild_index()
            return self.get_channel(class_name, channel_code)

        channel_infos = ChannelInfo.from_json(channel_set_info_path, channel_set_version)
        if channel_code is None:
            channel_infos = [ci for ci in channel_infos if ci.channelCode is None]
        else:
            channel_infos = [ci for ci in channel_infos if ci.channelCode == channel_code]

        if len(channel_infos) != 1:
            Logger.error("Found none or more than 1 matches for '%s' and '%s' in the channel index.",
                         class_name, channel_code or "None")
            return None
        else:
            Logger.debug("Found single channel in the channel index: %s.", channel_infos[0])

        if self.__is_channel_set_updated(channel_infos[0]):
            # let's see if the index has already been updated this section, of not, do it and
            # restart the ChannelRetrieval.
            if not self.__reindexed:
                # rebuild and restart
                Logger.warning("Re-index channel index due to channel_set update: %s.", channel_set_info_path)
                self.__rebuild_index()
            else:
                Logger.warning("Found updated channel_set: %s.", channel_set_info_path)

            # new we should init all channels by loading them all, just to be shure that all is ok
            Logger.debug("Going to fetching all channels to init them all.")
            self.get_channels()
            return self.get_channel(class_name, channel_code)

        if info_only:
            return channel_infos[0]

        return channel_infos[0].get_channel()

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

        # What platform are we
        platform = envcontroller.EnvController.get_platform()

        channels_updated = False
        country_visibility = {}

        for channel_set in self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY]:
            channel_set = self.__channelIndex[self.__CHANNEL_INDEX_CHANNEL_KEY][channel_set]
            channel_set_info_path = channel_set[self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
            channel_set_version = channel_set[self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]

            # Check if file exists. If not, rebuild index
            if not os.path.isfile(channel_set_info_path) and not self.__reindexed:
                Logger.warning("Missing channelSet file: %s.", channel_set_info_path)
                self.__rebuild_index()
                return self.get_channels()

            channel_infos = ChannelInfo.from_json(channel_set_info_path, channel_set_version)

            # Check if the channel was updated
            if self.__is_channel_set_updated(channel_infos[0]):
                # let's see if the index has already been updated this section, of not, do it and
                # restart the ChannelRetrieval.
                if not self.__reindexed:
                    # rebuild and restart
                    Logger.warning("Re-index channel index due to channelSet update: %s.", channel_set_info_path)
                    self.__rebuild_index()
                    return self.get_channels()
                else:
                    Logger.warning("Found updated channelSet: %s.", channel_set_info_path)

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

                # valid channel for this platform ?
                if not channel_info.compatiblePlatforms & platform == platform:
                    Logger.warning("Not loading: %s -> platform '%s' is not compatible.",
                                   channel_info, Environments.name(platform))
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

    def __deploy_new_channels(self):
        """ Checks the deploy folder for new channels, if present, deploys them

        The last part of the folders in the deploy subfolder are considered the
        channel names. The other part is replaced with the <addon base name>.
        So if the deploy has a folder temp.channelOne and the addon is called
        plugin.video.retrospect it will be deployed to plugin.video.retrospect.channel.channelOne.

        The folders are intially removed and then re-created. If the folder in
        the deploy does not have a addon.xml it will not be imported.

        :return: Indication of new folders were deployed.
        :rtype: bool

        """

        # We keep the channels in the "channels" folder and don't move them anymore as we should
        # not be changing the Kodi addon folder.

        channel_path = os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH)
        if not os.path.exists(channel_path):
            Logger.info("Not cleaning up old add-on folders as there is no channel path: %s", channel_path)
            return False

        to_deploy = os.listdir(channel_path)
        for deploy in to_deploy:
            old_add_on_path = os.path.abspath(os.path.join(Config.rootDir, "..", deploy))
            if os.path.isdir(old_add_on_path):
                Logger.info("Removing old add-on %s from %s", deploy, old_add_on_path)
                shutil.rmtree(old_add_on_path)

        return False

        # We keep the channels in the "channels" folder and don't move them anymore as we should
        # not be changing the Kodi addon folder.
        #
        # Logger.debug("Checking for new channels to deploy")
        #
        # # location of new channels and list of subfolders
        # deploy_path = os.path.join(Config.rootDir, "deploy")
        # to_deploy = os.listdir(deploy_path)
        #
        # # addons folder, different for Kodi and XBMC4Xbox, without a repo we should just use this.
        # if True or envcontroller.EnvController.is_platform(Environments.Xbox):
        #     target_folder = os.path.abspath(
        #         os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
        #     internal_channels = True
        # else:
        #     target_folder = os.path.abspath(
        #         os.path.join(Config.rootDir, ".."))
        #     internal_channels = False
        #
        # deployed = False
        # for deploy in to_deploy:
        #     if deploy.startswith("."):
        #         continue
        #
        #     if not os.path.exists(target_folder):
        #         os.mkdir(target_folder)
        #
        #     source_path = os.path.join(deploy_path, deploy)
        #
        #     # find out if the scriptname is not plugin.video.retrospect and update
        #     deploy_parts = deploy.split(".")
        #     dest_deploy = "%s.channel.%s" % (Config.addonDir, deploy_parts[-1])
        #     destination_path = os.path.join(target_folder, dest_deploy)
        #     Logger.info("Deploying Channel Addon '%s' to '%s'", deploy, destination_path)
        #
        #     # should they be deleted it from the main add-ons folder
        #     if internal_channels and os.path.isdir(os.path.join(Config.rootDir, "..", dest_deploy)):
        #         Logger.info("Removing old add-on %s from %s", dest_deploy,
        #                     os.path.join(Config.rootDir, ".."))
        #         shutil.rmtree(os.path.join(Config.rootDir, "..", dest_deploy))
        #
        #     if os.path.exists(destination_path):
        #         Logger.info("Removing old channel at %s", destination_path)
        #         shutil.rmtree(destination_path)
        #
        #     # only update if there was a real addon
        #     if os.path.exists(os.path.join(source_path, "addon.xml")):
        #         shutil.move(source_path, destination_path)
        #     else:
        #         shutil.rmtree(source_path)
        #     deployed = True
        #
        # return deployed

    def __get_index(self):
        """ Loads the channel index and if there is none, makes sure one is created.

        Checks:
        1. Existence of the index
        2. Channel add-ons in the index vs actual add-ons

        :return: The current channel index.
        :rtype: dict

        """

        # if it was not already re-index and the bit was set
        if self.__reindex:
            if self.__reindexed:
                Logger.warning("Forced re-index set, but a re-index was already done previously. Not Rebuilding.")
            else:
                Logger.info("Forced re-index set. Rebuilding.")
                return self.__rebuild_index()

        if not os.path.isfile(self.__CHANNEL_INDEX):
            Logger.info("No index file found at '%s'. Rebuilding.", self.__CHANNEL_INDEX)
            return self.__rebuild_index()

        try:
            with io.open(self.__CHANNEL_INDEX, 'rt', encoding='utf-8') as fd:
                data = fd.read()

            index_json = JsonHelper(data, logger=Logger.instance())
            Logger.debug("Loaded index from '%s'.", self.__CHANNEL_INDEX)

            if not self.__is_index_consistent(index_json.json):
                return self.__rebuild_index()
            return index_json.json
        except:
            Logger.critical("Error reading channel index. Rebuilding.", exc_info=True)
            return self.__rebuild_index()

    def __rebuild_index(self):
        """ Rebuilds the channel index that contains all channels and performs all necessary steps:

        1. Find all channel add-on paths and determine the version of the channel add-on
        2. For all channel sets in the add-on:
            a. See if it is a new channel set (pyo and pyc check)
            b. If so, initialise the channel set and then perform the first time actions on
               the included channels.
            c. Add all channels within the channel set to the channelIndex

        Remark: this method only generates the index of the channels, it does not import at all!

        :return: The current channel index.
        :rtype: dict

        """

        if self.__reindexed:
            Logger.error("Channel index was already re-indexed this run. Not doing it again.")
            return self.__channelIndex

        Logger.info("Rebuilding the channel index.")
        index = {
            self.__CHANNEL_INDEX_ADD_ONS_KEY: [],
            self.__CHANNEL_INDEX_CHANNEL_KEY: {}
        }

        # iterate all Retrospect Video Add-ons
        addon_path = self.__get_addon_path()
        channel_path_start = "%s.channel" % (Config.addonDir,)
        add_ons = [x for x in os.listdir(addon_path) if channel_path_start in x and "BUILD" not in x]
        for add_on_dir in add_ons:
            index[self.__CHANNEL_INDEX_ADD_ONS_KEY].append(add_on_dir)

            channel_add_on_path = os.path.join(addon_path, add_on_dir)
            channel_add_on_id, channel_add_on_version = self.__validate_add_on_version(channel_add_on_path)
            if channel_add_on_id is None:
                continue

            channel_sets = os.listdir(channel_add_on_path)
            for channel_set in channel_sets:
                if not os.path.isdir(os.path.join(channel_add_on_path, channel_set)):
                    continue

                channel_set_id = "chn_%s" % (channel_set,)
                Logger.debug("Found channel set '%s'", channel_set_id)
                index[self.__CHANNEL_INDEX_CHANNEL_KEY][channel_set_id] = {
                    self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY: str(channel_add_on_version),
                    self.__CHANNEL_INDEX_CHANNEL_INFO_KEY: os.path.join(channel_add_on_path, channel_set, "%s.json" % (channel_set_id,))
                }

        with io.open(self.__CHANNEL_INDEX, 'wt+', encoding='utf-8') as f:
            f.write(JsonHelper.dump(index))

        # now we marked that we already re-indexed.
        self.__reindexed = True
        self.__channelIndex = index
        Logger.info("Rebuilding channel index completed with %d channelSets and %d add-ons: %s.",
                    len(index[self.__CHANNEL_INDEX_CHANNEL_KEY]),
                    len(index[self.__CHANNEL_INDEX_ADD_ONS_KEY]),
                    index)

        envcontroller.EnvController.update_local_addons_in_kodi()
        return index

    def __validate_add_on_version(self, path):
        """ Parses the addon.xml file and checks if all is OK.

        :param str|unicode path:    The path to load the addon from.

        :return: the AddonId-Version
        :rtype: tuple[str|unicode|none,str|unicode|none]

        """

        addon_file = os.path.join(path, "addon.xml")

        # continue if no addon.xml exists
        if not os.path.isfile(addon_file):
            Logger.info("No addon.xml found at %s.", addon_file)
            return None, None

        with io.open(addon_file, 'rt+', encoding='utf-8') as f:
            addon_xml = f.read()

        pack_version = Regexer.do_regex('id="([^"]+)"\\W+version="([^"]+)"', addon_xml)
        if len(pack_version) > 0:
            # Get the first match
            pack_version = pack_version[0]
            package_id = pack_version[0]
            package_version = Version(version=pack_version[1])
            if Config.version.equal_builds(package_version):
                Logger.info("Adding %s version %s", package_id, package_version)
                return package_id, package_version
            else:
                Logger.warning("Skipping %s version %s: Versions do not match.",
                               package_id, package_version)
                return None, None
        else:
            Logger.critical("Cannot determine Channel Add-on version. Not loading Add-on @ '%s'.",
                            path)
            return None, None

    def __get_addon_path(self):
        """ Returns the path that holds all the Kodi add-ons. It differs for Xbox and other platforms.

        :return: The add-on base path
        :rtype: str|unicode

        """

        # different paths for Kodi and XBMC4Xbox
        # if envcontroller.EnvController.is_platform(Environments.Xbox) or :
        if os.path.isdir(os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH)):
            addon_path = os.path.abspath(os.path.join(Config.rootDir, self.__INTERNAL_CHANNEL_PATH))
        else:
            addon_path = os.path.abspath(os.path.join(Config.rootDir, ".."))

        return addon_path

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
                XbmcWrapper.show_dialog(title, channel_info.firstTimeMessage.split("|"))
            else:
                Logger.debug("Not showing first time message due to add-on setting set to '%s'.",
                             hide_first_time)
        return

    def __is_index_consistent(self, index):
        """ A quick check if a given Channel Index is correct.

        :param dict index:  A index with Channel information.

        :return: An indication (True/False) if the index is consistent.
        :rtype: bool

        """

        if self.__CHANNEL_INDEX_CHANNEL_KEY not in index:
            Logger.warning("Channel Index Inconsistent: missing '%s' key.", self.__CHANNEL_INDEX_CHANNEL_INFO_KEY)
            return False

        if self.__CHANNEL_INDEX_ADD_ONS_KEY not in index:
            Logger.warning("Channel Index Inconsistent: missing '%s' key.", self.__CHANNEL_INDEX_ADD_ONS_KEY)
            return False

        # verify if the channels add-ons match, otherwise it is invalid anyways
        indexed_channel_add_ons = index[self.__CHANNEL_INDEX_ADD_ONS_KEY]
        addon_path = self.__get_addon_path()
        channel_path_start = "%s.channel" % (Config.addonDir,)
        add_ons = [x for x in os.listdir(addon_path) if x.startswith(channel_path_start)]

        # see if the numbers match
        if len(indexed_channel_add_ons) != len(add_ons):
            Logger.warning("Channel Index Inconsistent: add-on count is not up to date (index=%s vs actual=%s).",
                           len(indexed_channel_add_ons), len(add_ons))
            return False
        # cross reference by putting them on a big pile and then get the distinct values (set) and
        # compare the length of the distinct values.
        if len(set(indexed_channel_add_ons + add_ons)) != len(add_ons):
            Logger.warning("Channel Index Inconsistent: add-on content is not up to date.")
            return False

        # Validate the version of the add-on and the channel-sets
        channels = index[self.__CHANNEL_INDEX_CHANNEL_KEY]
        first_version = channels[list(channels.keys())[0]][self.__CHANNEL_INDEX_CHANNEL_VERSION_KEY]
        first_version = Version(first_version)
        if not Config.version.equal_builds(first_version):
            Logger.warning("Inconsisten version 'index' vs 'add-on': %s vs %s", first_version, Config.version)
            return False

        first_path = channels[list(channels.keys())[0]][self.__CHANNEL_INDEX_CHANNEL_INFO_KEY]
        if not first_path.startswith(Config.rootDir.rstrip(os.sep)):
            Logger.warning("Inconsisten path for ChannelSet and main add-on:\n"
                           "Channel: '%s'\n"
                           "Add-on:  '%s'", first_path, Config.rootDir)
            return False

        return True

    def __str__(self):
        """ String representation of the object.

        :return: String representation of the object.
        :type: str|unicode

        """

        return "ChannelIndex for {} (id={})".format(Config.profileDir, self.id)
