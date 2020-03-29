# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import sys
import time
import struct

import xbmc
import xbmcaddon

from resources.lib.logger import Logger
from resources.lib.environments import Environments
from resources.lib.retroconfig import Config

# Only needed if we want to reinstate my own Kodi repository
# from xbmcwrapper import XbmcWrapper
# from helpers.languagehelper import LanguageHelper


class EnvController:
    """Controller class for getting all kinds of information about the
    Kodi environment."""

    __CurrentPlatform = None
    __SQLiteEnabled = None

    def __init__(self, logger=None):
        """Class to determine platform depended stuff

        :param Logger logger: a logger object that is used to log information to

        """

        self.logger = logger

    def print_retrospect_settings_and_folders(self, config, setting_info):
        """Prints out all the XOT related directories to the logFile.

        This method is mainly used for debugging purposes to provide developers a better insight
        into the system of the user.

        :param Type[Config] config:   The Retrospect config object.
        :param setting_info:          The AddonSettings object

        """

        # if we have a log level higher then debug, there is no need to do this
        if Logger.instance().minLogLevel > Logger.LVL_DEBUG:
            Logger.info("Not walking directory structure because the loglevel is set to INFO or higher")
            return

        directory = "<Unknown>"
        try:
            # in order to minimize the number of method resolves for os.path.join
            # we create a shortcut for it.
            ospathjoin = os.path.join

            version = xbmc.getInfoLabel("system.buildversion")
            build_date = xbmc.getInfoLabel("system.builddate")

            info_string = "%s: %s" % ("Version", version)
            info_string = "%s\n%s: %s" % (info_string, "BuildDate", build_date)
            info_string = "%s\n%s: %s" % (info_string, "Environment", self.__get_environment())
            info_string = "%s\n%s: %s" % (info_string, "Platform", self.get_platform(True))
            info_string = "%s\n%s: %s" % (info_string, "Python Version", self.__get_python_version())
            info_string = "%s\n%s: %s" % (info_string, "Retrospect Version", config.version)
            info_string = "%s\n%s: %s" % (info_string, "AddonID", config.addonId)
            info_string = "%s\n%s: %s" % (info_string, "Path", config.rootDir)
            info_string = "%s\n%s: %s" % (info_string, "ProfilePath", config.profileDir)
            info_string = "%s\n%s: %s" % (info_string, "PathDetection", config.pathDetection)
            info_string = "%s\n%s: %s" % (info_string, "Encoding", sys.getdefaultencoding())
            info_string = "%s\n%s: %s" % (info_string, "Widevine Path", self.widevine_lib())
            info_string = "%s\n%s: %s" % (info_string, "TextureMode", config.textureMode)
            if config.textureUrl:
                info_string = "%s\n%s: %s" % (info_string, "TextureUrl", config.textureUrl)

            self.logger.info("Kodi Information:\n%s", info_string)

            # log the settings
            self.logger.info("Retrospect Settings:\n%s", setting_info.print_setting_values())

            if setting_info.get_log_level() > 10:
                return

            # get the script directory
            dir_script = config.addonDir
            walk_source_path = os.path.abspath(ospathjoin(config.rootDir, ".."))
            dir_print = "Folder Structure of %s (%s)" % (config.appName, dir_script)

            # instead of walking all directories and files and then see if the
            # folders is in the exclude list, we first list the first children.
            # Then if the child folders contains the dir_script then, walk all
            # the subfolders and files. This greatly improves performance.
            for current_path in os.listdir(walk_source_path):
                self.logger.trace("Checking %s", current_path)
                if dir_script not in current_path:
                    continue

                self.logger.trace("Now walking DirectoryPrinter")
                dir_walker = os.walk(ospathjoin(walk_source_path, current_path))

                for directory, folders, files in dir_walker:  # @UnusedVariables
                    # if directory.count(excludePattern) == 0:
                    if directory.count("BUILD") != 0:
                        continue

                    for file_name in files:
                        if file_name.startswith(".") or file_name.endswith(".pyo") or file_name.endswith(".pyc"):
                            continue
                        dir_print = "%s\n%s" % (dir_print, ospathjoin(directory, file_name))
            self.logger.debug("%s" % (dir_print,))
        except:
            self.logger.critical("Error printing folder %s", directory, exc_info=True)

    def widevine_lib(self):
        """ Retrieve the path of the Widevine libraries.

        :return: The full path to either libwidevinecdm.so, widevinecdm.dll or libwidevinecdm.dylib
        :rtype: str

        """

        try:
            input_stream_adaptive_id = 'inputstream.adaptive'
            if not xbmc.getCondVisibility('System.HasAddon("{}")'.format(input_stream_adaptive_id)):
                return "<no-addon>"

            addon = xbmcaddon.Addon(input_stream_adaptive_id)
            decrypter_path_from_settings = addon.getSetting('DECRYPTERPATH')
            if decrypter_path_from_settings:
                cdm_path = xbmc.translatePath(decrypter_path_from_settings)
            else:
                cdm_path = os.path.join(xbmc.translatePath("special://home/"), "cdm")

            if not os.path.isdir(cdm_path):
                return "<none>"

            Logger.debug("Found CDM folder: %s", cdm_path)
            widevine_libs = [f for f in os.listdir(cdm_path) if f in
                             ("libwidevinecdm.so", "widevinecdm.dll", "libwidevinecdm.dylib")]

            return os.path.join(cdm_path, widevine_libs[0]) if len(widevine_libs) == 1 else "<none>"
        except:
            Logger.error("Error determining Widevine lib path.", exc_info=True)
            return "<error>"

    @staticmethod
    def get_platform(return_name=False):
        """ Returns the platform that Kodi returns as it's host:

        * linux   - Normal Linux
        * UWP     - Windows Store App
        * OS X    - Apple OS
        * Windows - Windows OS
        * unknown - in case it's undetermined

        :param bool return_name:    If true a string value is returned
        :return: A string representing the host OS:
        :rtype: int|str

        """

        if not EnvController.__CurrentPlatform:
            # let's cache the current environment as the call to the Kodi library is very slow.
            platform = Environments.Unknown
            # it's in the .\xbmc\GUIInfoManager.cpp
            if xbmc.getCondVisibility("system.platform.linux"):
                platform = Environments.Linux
            elif xbmc.getCondVisibility("system.platform.uwp"):
                platform = Environments.UWP
            elif xbmc.getCondVisibility("system.platform.windows"):
                platform = Environments.Windows
            elif xbmc.getCondVisibility("system.platform.ios"):
                platform = Environments.IOS
            elif xbmc.getCondVisibility("system.platform.tvos"):
                platform = Environments.TVOS
            elif xbmc.getCondVisibility("system.platform.osx"):
                platform = Environments.OSX
            elif xbmc.getCondVisibility("system.platform.android"):
                platform = Environments.Android

            EnvController.__CurrentPlatform = platform
            Logger.info("Current platform determined to be: %s", Environments.name(EnvController.__CurrentPlatform))

        if return_name:
            return Environments.name(EnvController.__CurrentPlatform)
        else:
            return EnvController.__CurrentPlatform

    @staticmethod
    def is_platform(platform):
        """Checks if the current platform matches the requested on

        :param int platform: The requested platform

        :return: True if the <platform> matches EnvController.get_platform().
        :rtype: bool

        """

        plat = EnvController.get_platform()

        # check if the actual platform is in the platform bitmask
        # return plat & platform  == platform
        return platform & plat == plat

    @staticmethod
    def cache_check():
        """Checks if the cache folder exists. If it does not exists it will be created.

        :return: False it the folder initially did not exist
        :rtype: bool

        """

        # check for cache folder. If not present. Create it!
        if not os.path.exists(Config.cacheDir):
            Logger.info("Creating cache folder at: %s", Config.cacheDir)
            os.makedirs(Config.cacheDir)
            return False

        return True

    @staticmethod
    def cache_clean_up(path, cache_time, mask="*.*"):
        """Cleans up the XOT cache folder.

        Check the cache files create timestamp and compares it with the current datetime extended
        with the amount of seconds as defined in cacheTime.

        Expired items are deleted.
        :param str path:        The cache path to clean.
        :param int cache_time:  The minimum (in seconds) of files that will be deleted.
        :param str mask:        The file mask to consider when cleaning the cache.

        """

        # let's import htis one here
        import fnmatch

        try:
            Logger.info("Cleaning up cache in '%s' that is older than %s days",
                        os.path.join(path, "**", mask), cache_time / 24 / 3600)

            if not os.path.exists(path):
                Logger.info("Did not cleanup cache: folder does not exist")
                return

            delete_count = 0
            file_count = 0

            #for item in os.listdir(path):
            current_dir = None
            for root, dirs, files in os.walk(path):
                if current_dir != root:
                    Logger.debug("Cleaning cache folder: %s", root)
                    current_dir = root

                for basename in files:
                    if fnmatch.fnmatch(basename, mask):
                        filename = os.path.join(root, basename)
                        Logger.trace("Inspecting: %s", filename)
                        file_count += 1
                        create_time = os.path.getctime(filename)
                        if create_time + cache_time < time.time():
                            os.remove(filename)
                            Logger.debug("Removed file: %s", filename)
                            delete_count += 1

            Logger.info("Removed %s of %s files from cache in: '%s'", delete_count, file_count, path)
        except:
            Logger.critical("Error cleaning the cachefolder: %s", path, exc_info=True)

    def __get_python_version(self):
        """Returns the current python version

        Returns:
        Python version in the #.#.# format

        """

        major = sys.version_info[0]
        minor = sys.version_info[1]
        build = sys.version_info[2]
        return "%s.%s.%s" % (major, minor, build)

    def __get_environment(self):
        """ Gets the type of environment for Kodi in a string:

        * Linux   - Normal Linux
        * Linux64 - 64-bit Linux
        * OS X    - For Apple devices
        * win32   - Windows / UWP

        :return: String representation for the current environment.

        """

        is_x64 = struct.calcsize("P") == 8

        env = os.environ.get("OS", "win32")
        if env == "Linux":
            if is_x64:
                return "Linux64"
            return "Linux"

        elif env == "OS X":
            return "OS X"

        else:
            if is_x64:
                return "Win64"

            return "Win32"
