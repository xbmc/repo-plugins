# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
import io
import sys

import xbmcgui


from resources.lib.environments import Environments
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.logger import Logger
from resources.lib.retroconfig import Config
from resources.lib.addonsettings import AddonSettings
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.textures import TextureHandler


class ChannelInfo(object):
    __channel_cache = dict()

    def __init__(self, guid, name, description, icon, category, path,
                 channel_code=None, sort_order=255, language=None,
                 compatible_platforms=Environments.All, fanart=None):
        """ Creates a ChannelInfo object with basic information for a channel

        :param str guid:                    A unique GUID.
        :param str name:                    The channel name.
        :param str description:             The channel description.
        :param str icon:                    Name of the icon.
        :param str category:                The category it belongs to.
        :param str path:                    Path of the channel.
        :param str channel_code:            A code that distinguishes a channel within a module.
                                            Default is None.
        :param int sort_order:              The sortorder (0-255). Default is 255.
        :param str language:                The language of the channel. Default is None.
        :param int compatible_platforms:    The supported Platform ID taken from Environments.
                                            Default is Environments.All
        :param str fanart:                  A fanart url/path.

        """

        # set the path info
        self.path = os.path.dirname(path)
        path_parts = path.split(os.sep)
        self.moduleName = os.path.splitext(path_parts[-1])[0]

        self.id = ("%s.%s.%s" % (path_parts[-3], path_parts[-2], channel_code or "")).rstrip(".")
        # TODO: the GUID could be replaced by the self.id in the future.
        self.guid = guid
        self.channelName = name
        self.channelCode = channel_code
        self.channelDescription = description

        self.category = category
        self.compatiblePlatforms = compatible_platforms
        self.language = language
        self.sortOrder = sort_order
        # I am Dutch, sorry about that
        if language == "nl":
            self.sortOrderPerCountry = "#_%s.%04d" % (language or "zz", sort_order)
        else:
            self.sortOrderPerCountry = "#%s.%04d" % (language or "zz", sort_order)
        self.firstTimeMessage = None

        self.settings = []
        self.localIPSupported = False
        self.addonUrl = None

        self.icon = icon
        self.fanart = fanart
        self.version = "x.x.x.x"
        self.enabled = False                  # enabled from the settings
        self.visible = False                  # hidden/visible due to country settings
        self.adaptiveAddonSelectable = False  # can the InputStream Adaptive be selected

    @property
    def sort_key(self):
        return "{0}-{1}".format(self.sortOrderPerCountry, self.channelName)

    def get_channel(self):
        """ Instantiates a channel from a ChannelInfo object 

        :returns: an instantiated Channel object based on this ChannelInfo object.

        """

        Logger.trace("Importing module %s from path %s", self.moduleName, self.path)

        sys.path.append(self.path)
        exec("import {}".format(self.moduleName))

        channel_command = '%s.Channel(self)' % (self.moduleName,)
        try:
            Logger.trace("Running command: %s", channel_command)
            channel = eval(channel_command)
        except:
            Logger.error("Cannot Create channel for %s", self, exc_info=True)
            return None
        return channel

    @property
    def safe_name(self):
        """  Property to retrieve a safe name that can be used within Kodi.

        :returns: the channel name in a format that can be safely be used in the Kodi settings and will not cause
                  any issues with the boolean expressions there.
        :rtype: str
        """

        return self.channelName.replace("(", "[").replace(")", "]")

    def get_kodi_item(self):
        """ Creates an Kodi ListItem object for this channel
        
        :return: a Kodi ListItem with all required properties set.
        :rtype: xbmcgui.ListItem

        """

        name = HtmlEntityHelper.convert_html_entities(self.channelName)
        description = HtmlEntityHelper.convert_html_entities(self.channelDescription)

        if self.uses_external_addon:
            from resources.lib.xbmcwrapper import XbmcWrapper
            name = "{} {}".format(name, XbmcWrapper.get_external_add_on_label(self.addonUrl))

        self.icon = self.__get_image_path(self.icon)
        item = xbmcgui.ListItem(name, description)
        item.setArt({'thumb': self.icon, 'icon': self.icon})

        # http://mirrors.kodi.tv/docs/python-docs/14.x-helix/xbmcgui.html#ListItem-setInfo
        item.setInfo("video", {"Title": name,
                               # "Count": self.sortOrderPerCountry,
                               # "TrackNumber": self.sortOrder,
                               "Genre": LanguageHelper.get_full_language(self.language),
                               # "Tagline": description,
                               "Plot": description})

        if AddonSettings.hide_fanart():
            return item

        if self.fanart is not None:
            self.fanart = self.__get_image_path(self.fanart)
        else:
            self.fanart = os.path.join(Config.rootDir, "fanart.jpg")
        item.setArt({'fanart': self.fanart})
        return item

    def __str__(self):
        """Returns a string representation of the current channel.

        :return: String representation for this object
        :rtype: str

        """

        if self.channelCode is None:
            return "%s [%s-%s=%s, %s=%s, %s, %s] (Order: %s)" % (
                self.channelName, self.id, self.version, self.enabled, self.language,
                self.visible, self.category, self.guid, self.sortOrderPerCountry
            )
        else:
            return "%s (%s) [%s-%s=%s, %s=%s, %s, %s] (Order: %s)" % (
                self.channelName, self.channelCode, self.id, self.version, self.enabled,
                self.language, self.visible, self.category, self.guid, self.sortOrderPerCountry
            )

    def __repr__(self):
        """ Technical representation

        :return: Technical string representation for this object
        :rtype: str

        """

        return "%s @ %s\nmoduleName: %s\nicon: %s\ncompatiblePlatforms: %s" % (
            self, self.path, self.moduleName,
            self.icon, self.compatiblePlatforms
        )

    def __eq__(self, other):
        """Compares to channel objects for equality

        The comparison is based only on the self.guid of the channels.

        :param ChannelInfo other: The other object to compare
        :return: Whether other equals self
        :rtype: bool

        """

        if other is None:
            return False

        return self.guid == other.guid

    def __get_image_path(self, image):
        """ Tries to determine the path of an image

        Arguments:
        image : String - The filename (not path) of the image

        Returns the path of the image. In case of a Kodi skin image it will
        return just the filename, else the full path.

        """

        return TextureHandler.instance().get_texture_uri(self, image)

    @property
    def uses_external_addon(self):
        return self.addonUrl is not None

    @staticmethod
    def from_json(path, version="x.x.x.x"):
        """ Generates a list of ChannelInfo objects present in the json meta data file.

        :param str path: The path of the json file.
        :param str version: Version of the channel set that contains the channel info file.

        :return: The channel info objects within the json file.
        :rtype: list[ChannelInfo]

        """

        if path in ChannelInfo.__channel_cache:
            Logger.debug("Fetching ChannelInfo from ChannelInfo Cache for '%s'", path)
            return ChannelInfo.__channel_cache[path]

        channel_infos = []

        with io.open(path, mode="r", encoding="utf-8") as json_file:
            json_data = json_file.read()

        json = JsonHelper(json_data, logger=Logger.instance())
        channels = json.get_value("channels")

        if "settings" in json.json:
            settings = json.get_value("settings")
        else:
            settings = []
        Logger.debug("Found %s channels and %s settings in %s", len(channels), len(settings), path)

        for channel in channels:
            channel_info = ChannelInfo(channel["guid"],
                                       channel["name"],
                                       channel["description"],
                                       channel["icon"],
                                       channel["category"],
                                       path,

                                       # none required items
                                       channel.get("channelcode", None),
                                       channel.get("sortorder", 255),
                                       channel.get("language", None),
                                       eval(channel.get("compatible", "Environments.All")),
                                       channel.get("fanart", None))
            channel_info.firstTimeMessage = channel.get("message", None)
            channel_info.addonUrl = channel.get("addonUrl", None)
            channel_info.adaptiveAddonSelectable = channel.get("adaptiveAddonSelectable", False)
            # Disable spoofing for the moment
            # channel_info.localIPSupported = channel.get("localIPSupported", False)
            channel_info.settings = settings
            channel_info.version = version

            # validate a bit
            if channel_info.channelCode == "None":
                raise Exception("'None' as channelCode")
            if channel_info.language == "None":
                raise Exception("'None' as language")

            channel_infos.append(channel_info)

        ChannelInfo.__channel_cache[path] = channel_infos
        return channel_infos
