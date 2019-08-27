# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import random

from logger import Logger
from pickler import Pickler


class ParameterParser(object):
    def __init__(self, addon_name, params):
        """

        :param str addon_name:  The name of the add-on
        :param str params:      The parameteters used to start the ParameterParser

        """

        Logger.debug("Parsing parameters from: %s", params)

        # Url Keywords
        self.keywordPickle = "pickle"                                   # : Used for the pickle item
        self.keywordAction = "action"                                   # : Used for specifying the action
        self.keywordChannel = "channel"                                 # : Used for the channel
        self.keywordChannelCode = "channelcode"                         # : Used for the channelcode
        self.keywordCategory = "category"                               # : Used for the category
        self.keywordRandomLive = "rnd"                                  # : Used for randomizing live items
        self.keywordSettingId = "settingid"                             # : Used for setting an encrypted setting
        self.keywordSettingActionId = "settingactionid"                 # : Used for passing the actionid for the encryption
        self.keywordSettingName = "settingname"                         # : Used for setting an encrypted settings display name
        self.keywordSettingTabFocus = "tabfocus"                        # : Used for setting the tabcontrol to focus after changing a setting
        self.keywordSettingSettingFocus = "settingfocus"                # : Used for setting the setting control to focus after changing a setting
        self.keywordLanguage = "lang"                                   # : Used for the 2 char language information
        self.keywordProxy = "proxy"                                     # : Used so set the proxy index
        self.keywordLocalIP = "localip"                                 # : Used to set the local ip index

        # Url Actions
        self.actionFavourites = "favourites"                            # : Used to show favorites for a channel
        self.actionAllFavourites = "allfavourites"                      # : Used to show all favorites
        self.actionRemoveFavourite = "removefromfavourites"             # : Used to remove items from favorites
        self.actionAddFavourite = "addtofavourites"                     # : Used to add items to favorites
        self.actionDownloadVideo = "downloadVideo"                      # : Used to download a video item
        self.actionPlayVideo = "playvideo"                              # : Used to play a video item
        self.actionUpdateChannels = "updatechannels"                    # : Used to update channels
        self.actionListFolder = "listfolder"                            # : Used to list a folder
        self.actionListCategory = "listcategory"                        # : Used to show the channels from a category
        self.actionConfigureChannel = "configurechannel"                # : Used to configure a channel
        self.actionSetEncryptionPin = "changepin"                       # : Used for setting an application pin
        self.actionSetEncryptedValue = "encryptsetting"                 # : Used for setting an application pin
        self.actionResetVault = "resetvault"                            # : Used for resetting the vault
        self.actionPostLog = "postlog"                                  # : Used for sending log files to pastebin.com
        self.actionProxy = "setproxy"                                   # : Used for setting a proxy

        self.propertyRetrospect = "Retrospect"
        self.propertyRetrospectChannel = "RetrospectChannel"
        self.propertyRetrospectChannelSetting = "RetrospectChannelSettings"
        self.propertyRetrospectFolder = "RetrospectFolder"
        self.propertyRetrospectVideo = "RetrospectVideo"
        self.propertyRetrospectCloaked = "RetrospectCloaked"
        self.propertyRetrospectCategory = "RetrospectCategory"
        self.propertyRetrospectFavorite = "RetrospectFavorite"
        self.propertyRetrospectAdaptive = "RetrospectAdaptive"

        # determine the query parameters
        self.params = self.__get_parameters(params)
        self.pluginName = addon_name

        # We need a picker for this instance
        self._pickler = Pickler()

    def _create_action_url(self, channel, action, item=None, category=None):
        """ Creates an URL that includes an action.

        Arguments:
        channel : Channel -
        action  : string  -

        Keyword Arguments:
        item : MediaItem -

        :param ChannelInfo|Channel channel:     The channel object to use for the URL.
        :param str action:                      Action to create an url for
        :param MediaItem item:                  The media item to add
        :param str category:                    The category to use.

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
            params[self.keywordChannel] = channel.moduleName
            if channel.channelCode:
                params[self.keywordChannelCode] = channel.channelCode

        params[self.keywordAction] = action

        # it might have an item or not
        if item is not None:
            params[self.keywordPickle] = self._pickler.pickle_media_item(item)

            if action == self.actionPlayVideo and item.isLive:
                params[self.keywordRandomLive] = random.randint(10000, 99999)

        if category:
            params[self.keywordCategory] = category

        url = "%s?" % (self.pluginName, )
        for k in params.keys():
            url = "%s%s=%s&" % (url, k, params[k])

        url = url.strip('&')
        # Logger.Trace("Created url: '%s'", url)
        return url

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
            if self.keywordChannelCode not in result:
                Logger.debug("Adding ChannelCode=None as it was missing from the dict: %s", result)
                result[self.keywordChannelCode] = None
        except:
            Logger.critical("Cannot determine query strings from %s", query_string, exc_info=True)
            raise

        return result
