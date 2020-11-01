# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.textures import TextureHandler


class Remote(TextureHandler):
    def __init__(self, cdn_url, logger):
        TextureHandler.__init__(self, logger)

        self.__cdnUrl = cdn_url
        if not self.__cdnUrl:
            self.__cdnUrl = "https://cdn.rieter.net/plugin.video.retrospect.cdn/"

    def _purge_texture_cache(self, channel_path):
        """ Removes those entries from the textures cache that are no longer required.

        :param str channel_path:  the channel path

        """

        cdn_folder = self._get_cdn_sub_folder(channel_path)
        self._logger.info("Purging Kodi Texture for: %s", cdn_folder)
        self._purge_kodi_cache(cdn_folder)
        return

    def _get_texture_uri(self, channel_path, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling,
        it might also cache the texture and return that path.

        :param str channel_path:    the path of the channel's to which the file belongs
        :param str file_name:       the file name

        :returns: the local url/path to the file
        :rtype: str

        """

        if file_name is None or file_name == "":
            return file_name

        if file_name.startswith("http"):
            return_value = file_name
        else:
            cdn_folder = self._get_cdn_sub_folder(channel_path)
            return_value = "%s/%s/%s" % (self.__cdnUrl, cdn_folder, file_name)

        self._logger.debug("Resolved texture '%s' to '%s'", file_name, return_value)
        return return_value

    def is_texture_or_empty(self, uri):
        """ Returns whether the uri points to a local resource or remote

        :param str uri: The URI for the texture

        :returns: Indicator whether or not the resource is local
        :rtype: bool

        """

        if not uri:
            return True

        return uri.startswith(self.__cdnUrl)
