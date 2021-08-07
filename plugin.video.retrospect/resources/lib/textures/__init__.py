# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.xbmcwrapper import XbmcWrapper
from resources.lib.helpers.jsonhelper import JsonHelper

__all__ = ["local", "remote", "TextureHandler"]

Local = "local"
Remote = "remote"
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

    # noinspection PyUnusedLocal
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
        elif mode == Resources:
            from . import resourceaddon
            TextureHandler.__TextureHandler = resourceaddon.Resources(config.textureResource, logger)
        else:
            raise Exception("Invalide mode: %s" % (mode,))

        return TextureHandler.__TextureHandler

    def get_texture_uri(self, channel, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling,
        it might also cache the texture and return that path.

        :param ChannelInfo|Channel channel:     the channel to which the file belongs.
        :param str file_name:                   the file name

        :return: The full URI to the local resource of the file.
        :rtype: str

        """

        return self._get_texture_uri(channel.path, file_name)

    def _get_texture_uri(self, channel_path, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling,
        it might also cache the texture and return that path.

        :param str channel_path:    the path of the channel's to which the file belongs
        :param str file_name:       the file name

        :returns: the local url/path to the file
        :rtype: str

        """
        raise NotImplementedError

    def purge_texture_cache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        :param ChannelInfo|Channel channel:     the channel to which the file belongs.

        """

        return self._purge_texture_cache(channel.path)

    def _purge_texture_cache(self, channel_path):
        """ Removes those entries from the textures cache that are no longer required.

        :param str channel_path:  the channel path

        """

        raise NotImplementedError

    def is_texture_or_empty(self, uri):
        """ Returns whether the uri points to a local resource or remote

        :param str uri: The URI for the texture

        :returns: Indicator whether or not the resource is local
        :rtype: bool

        """

        raise NotImplementedError

    def _purge_kodi_cache(self, channel_texture_path):
        """ Class the JSON RPC within Kodi that removes all changed items which paths contain the
        value given in channelTexturePath

        :param str channel_texture_path:  The path that is used to search textures in Kodi.

        The path can be a partial path to use int he json RPC.

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
