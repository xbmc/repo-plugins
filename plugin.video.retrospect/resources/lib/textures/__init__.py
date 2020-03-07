# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.retroconfig import Config

__all__ = ["local", "remote", "cached", "TextureHandler"]

Local = "local"
Remote = "remote"
Cached = "cached"
Resources = "resources"


class TextureHandler:
    __TextureHandler = None

    def __init__(self, logger):
        """ Initialize the texture base

        @param logger:      A logger to log stuff.

        """

        self._logger = logger               # : a logger
        self._addonId = None                # : the addon ID

        # some dictionaries for caching
        self.__cdnPaths = {}
        self.__addonIds = {}

    @staticmethod
    def instance():
        """ Returns the TextureHandler singleton

        :return: The TextureHandler
        :rtype: TextureHandler

        """

        return TextureHandler.__TextureHandler

    @staticmethod
    def set_texture_handler(config, logger, uri_handler=None):
        """ Fetches a TextureManager for specific mode and channel.

        @param config:              The Retrospect Config object
        @param logger:              An Logger
        @param uri_handler:          The UriHandler

        @return: A TextureHandler object for the requested mode

        """

        mode = config.textureMode.lower()
        if logger is not None:
            logger.trace("Creating '%s' Texture Mananger", mode)

        if mode == Local:
            from . import local
            TextureHandler.__TextureHandler = local.Local(logger)
        elif mode == Remote:
            from . import remote
            TextureHandler.__TextureHandler = remote.Remote(config.textureUrl, logger)
        elif mode == Cached:
            from . import cached
            TextureHandler.__TextureHandler = cached.Cached(config.textureUrl,
                                                            config.profileDir, config.profileUri,
                                                            logger, uri_handler)
        elif mode == Resources:
            from . import resourceaddon
            TextureHandler.__TextureHandler = resourceaddon.Resources(config.textureResource, logger)
        else:
            raise Exception("Invalide mode: %s" % (mode,))

        return TextureHandler.__TextureHandler

    def get_texture_uri(self, channel, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param file_name: the file name
        @param channel:  the channel

        """

        # Should be implemented
        pass

    def number_of_missing_textures(self):
        """ Indication whether or not textures need to be retrieved.

        @return: a boolean value
        """

        # Could be implemented
        return 0

    def fetch_textures(self, dialog_call_back=None):
        """ Fetches all the needed textures

        @param dialog_call_back:  Callback method with signature
                                  Function(self, retrievedSize, totalSize, perc, completed, status)

        @return: the number of bytes fetched

        """

        # Could be implemented
        return 0

    def purge_texture_cache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        @param channel:  the channel

        """

        # Should be implemented
        pass

    def is_texture_or_empty(self, uri):
        """ Returns whether the uri points to a local resource or remote

        :param str uri: The URI for the texture

        :returns: Indicator whether or not the resource is local
        :rtype: bool

        """

        raise NotImplementedError

    def _get_cdn_sub_folder(self, channel):
        """ Determines the CDN folder, e.g.: channel.be.canvas

        @param channel: the channel to determine the CDN folder for.

        Remark: we cache some stuff for performance improvements

        """

        if channel.path in self.__cdnPaths:
            return self.__cdnPaths[channel.path]

        parts = channel.path.rsplit(os.sep, 2)[-2:]
        cdn = ".".join(parts)
        if cdn.startswith(Config.addonId):
            cdn = cdn[len(Config.addonId) + 1:]
        self.__cdnPaths[channel.path] = cdn
        return cdn

    def _purge_kodi_cache(self, channel_texture_path):
        """ Class the JSON RPC within Kodi that removes all changed items which paths contain the
        value given in channelTexturePath

        @param channel_texture_path: string - The

        """

        json_cmd = '{' \
                   '"jsonrpc": "2.0", ' \
                   '"method": "Textures.GetTextures", ' \
                   '"params": {' \
                   '"filter": {"operator": "contains", "field": "url", "value": "%s"}, ' \
                   '"properties": ["url"]' \
                   '}, ' \
                   '"id": "libTextures"' \
                   '}' % (channel_texture_path,)
        json_results = XbmcWrapper.execute_json_rpc(json_cmd, self._logger)

        results = JsonHelper(json_results, logger=self._logger)
        if "error" in results.json or "result" not in results.json:
            self._logger.error("Error retreiving textures:\nCmd   : %s\nResult: %s", json_cmd, results.json)
            return

        results = results.get_value("result", "textures", fallback=[])
        for result in results:
            texture_id = result["textureid"]
            texture_url = result["url"]
            self._logger.debug("Going to remove texture: %d - %s", texture_id, texture_url)
            json_cmd = '{' \
                       '"jsonrpc": "2.0", ' \
                       '"method": "Textures.RemoveTexture", ' \
                       '"params": {' \
                       '"textureid": %s' \
                       '}' \
                       '}' % (texture_id,)
            XbmcWrapper.execute_json_rpc(json_cmd, self._logger)
        return
