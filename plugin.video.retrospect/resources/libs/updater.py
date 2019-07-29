#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import re

from helpers.jsonhelper import JsonHelper
from version import Version
from logger import Logger


class Updater(object):
    __regex = None

    def __init__(self, update_url, current_version, uri_handler, logger, release_channel=True):
        """ Initiates a Updater class

        :param str update_url:              The URL to look for updates.
        :param Version current_version:     The current add-on version.
        :param any uri_handler:             The URL handler
        :param Logger logger:               A logger.
        :param int release_channel:        What release track are we on? Stable or experimental?
        """

        if not update_url:
            raise ValueError("Missing update url")
        if not current_version:
            raise ValueError("Missing current version")
        if not uri_handler:
            raise ValueError("Missing UriHandler")

        self.updateUrl = update_url
        self.currentVersion = current_version
        self.onlineVersion = None
        self.stableRelease = release_channel == 0

        self.__logger = logger
        self.__uriHandler = uri_handler

    def is_new_version_available(self):
        """ Check if a new version is available online.

        :return: Indication if a newer version is available
        :rtype: str

        """

        try:
            # We don't determine this ourselves.
            # are_we_pre_release = self.currentVersion.buildType is not None
            include_experimental = not self.stableRelease
            self.onlineVersion = self.__get_online_version(include_experimental)
            if self.onlineVersion is None:
                return False

            self.__logger.debug("Found online version: %s", self.onlineVersion)
            return self.currentVersion < self.onlineVersion
        except:
            self.__logger.error("Error checking for updates", exc_info=True)
            return False

    def __get_online_version(self, include_alpha_beta=False):
        """ Retrieves the current online version.

        :param bool include_alpha_beta: should we include alpha/beta releases?

        :return: Returns the current online version or `None` of no version was found.
        :rtype: None|Version

        """

        data = self.__uriHandler.open(self.updateUrl, no_cache=True)
        json_data = JsonHelper(data)
        online_downloads = [d for d in json_data.get_value("values") if self.__is_valid_update(d)]
        if len(online_downloads) == 0:
            return None

        max_version = None
        for online_download in online_downloads:
            online_parts = online_download['name'].rsplit(".", 1)[0].split("-")
            if len(online_parts) < 2:
                continue

            # fix the problem that a ~ is preventing downloads on BitBucket
            online_version_data = online_parts[1].replace("alpha", "~alpha").replace("beta", "~beta")
            online_version = Version(online_version_data)

            if not include_alpha_beta and online_version.buildType is not None:
                self.__logger.trace("Ignoring %s", online_version)
                continue

            self.__logger.trace("Found possible version: %s", online_version)
            if online_version > max_version:
                max_version = online_version

        return max_version

    def __is_valid_update(self, download):
        """ Checks if the found API entry is indeed an update.

        :param dict[str, Any] download: The information from the API.

        :return: Indication if the found download indeed points to a download.
        :rtype: bool

        """

        name = download.get("name")
        if name is None:
            return False

        if Updater.__regex is None:
            Updater.__regex = re.compile(
                r"^(?:plugin\.video\.retrospect|net\.rieter\.xot)-\d+\.\d+\.\d+(\.\d+)?(~?(alpha|beta)\d+)?\.zip",
                re.IGNORECASE)

        return Updater.__regex.match(name) is not None
