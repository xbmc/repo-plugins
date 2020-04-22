# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import random

from resources.lib.retroconfig import Config
from resources.lib.logger import Logger
from resources.lib.pickler import Pickler
from resources.lib.actions import keyword
from resources.lib.actions.action import PLAY_VIDEO
from resources.lib.mediaitem import MediaItem


class ActionParser(object):
    def __init__(self, addon_name, handle, params):
        """

        :param str addon_name:  The name of the add-on
        :param int handle:      The handle for this run
        :param str params:      The parameters used to start the ActionParser

        """

        Logger.debug("Parsing parameters from: %s", params)

        self.handle = int(handle)

        # determine the query parameters
        self._params = params
        self.params = self.__get_parameters(params)
        self.pluginName = addon_name

        # We need a picker for this instance
        self.pickler = Pickler(Config.profileDir)

        # Field for property
        self.__media_item = None

        # For remote debugging and log reading purpose we need the full pickle string.
        if Logger.instance().minLogLevel <= Logger.LVL_DEBUG \
                and self.media_item is not None \
                and self.pickler.is_pickle_store_id(self.params[keyword.PICKLE]):
            Logger.debug("Replacing PickleStore pickle '%s' with full pickle", self.params[keyword.PICKLE])
            self.params[keyword.PICKLE] = self.pickler.pickle_media_item(self.media_item)

    @property
    def media_item(self):
        """ The current MediaItem

        :returns: The current MediaItem
        :rtype: MediaItem

        """

        if self.__media_item is None and keyword.PICKLE in self.params:
            self.__media_item = self.pickler.de_pickle_media_item(self.params[keyword.PICKLE])

        return self.__media_item

    def create_action_url(self, channel, action, item=None, store_id=None, category=None):
        """ Creates an URL that includes an action.

        Arguments:
        channel : Channel -
        action  : string  -

        Keyword Arguments:
        item : MediaItem -

        :param ChannelInfo|Channel channel:     The channel object to use for the URL
        :param str action:                      Action to create an url for
        :param MediaItem item:                  The media item to add
        :param str store_id:                    The ID of the pickle store
        :param str category:                    The category to use

        :return: a complete action url with all keywords and values
        :rtype: str|unicode

        """

        if action is None:
            raise Exception("action is required")

        # catch the plugin:// url's for items and channels.
        if item is not None and item.url and item.url.startswith("plugin://"):
            return item.url

        if item is None and channel is not None and channel.uses_external_addon:
            return channel.addonUrl

        params = dict()
        if channel:
            params[keyword.CHANNEL] = channel.moduleName
            if channel.channelCode:
                params[keyword.CHANNEL_CODE] = channel.channelCode

        params[keyword.ACTION] = action

        # it might have an item or not
        if item is not None:
            params[keyword.PICKLE] = "{}--{}".format(store_id, item.guid)

            if action == PLAY_VIDEO and item.isLive:
                params[keyword.RANDOM_LIVE] = random.randint(10000, 99999)

        if category:
            params[keyword.CATEGORY] = category

        url = "%s?" % (self.pluginName, )
        for k in params.keys():
            url = "%s%s=%s&" % (url, k, params[k])

        url = url.strip('&')
        # Logger.Trace("Created url: '%s'", url)
        return url

    def get_parent_guid(self, channel, parent_item):
        """ Returns the parent guid of an item

        :param channel:         The parent channel object
        :param parent_item:     The parent items

        :return: a guid of either the parent channel or item
        :rtype: str

        """

        if channel is None and parent_item is None:
            # we should not use the store
            return None

        return channel.guid if parent_item is None else parent_item.guid

    def __get_parameters(self, query_string):
        """ Extracts the actual parameters as a dictionary from the passed in querystring.
        This method takes the self.quotedPlus into account.

        :param str query_string:    The querystring

        :return: dict() of keywords and values.
        :rtype: dict[str,str|None]

        """
        result = dict()
        query_string = query_string.strip('?')
        if query_string == '':
            return result

        try:
            for pair in query_string.split("&"):
                (k, v) = pair.split("=")
                result[k] = v

            # if the channelcode was empty, it was stripped, add it again.
            if keyword.CHANNEL_CODE not in result:
                Logger.debug("Adding ChannelCode=None as it was missing from the dict: %s", result)
                result[keyword.CHANNEL_CODE] = None
        except:
            Logger.critical("Cannot determine query strings from %s", query_string, exc_info=True)
            raise

        return result

    def __str__(self):
        return "Plugin Params: {} ({})\n" \
               "Handle:      {}\n" \
               "Name:        {}\n" \
               "Query:       {}".format(self.params, len(self.params), self.handle, self.pluginName, self._params)
