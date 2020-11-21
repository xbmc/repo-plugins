# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib.textures import TextureHandler


class Resources(TextureHandler):
    def __init__(self, resource_add_on, logger):
        TextureHandler.__init__(self, logger)

        self.__resource_add_on = resource_add_on

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
        elif file_name.startswith("resource://"):
            return_value = file_name
        else:
            cdn_folder = self._get_cdn_sub_folder(channel_path)
            return_value = "resource://%s/%s/%s" % (self.__resource_add_on, cdn_folder, file_name)

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

        return uri.startswith("resource://")

    def _purge_texture_cache(self, channel_path):
        """ Removes those entries from the textures cache that are no longer required.

        :param str channel_path:  the channel path

        """
        pass
