# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib.textures import TextureHandler


class Resources(TextureHandler):
    def __init__(self, resource_add_on, logger):
        TextureHandler.__init__(self, logger)

        self.__resource_add_on = resource_add_on

    def get_texture_uri(self, channel, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param file_name: the file name
        @param channel:  the channel

        """

        if file_name is None or file_name == "":
            return file_name

        if file_name.startswith("http"):
            return_value = file_name
        elif file_name.startswith("resource://"):
            return_value = file_name
        else:
            cdn_folder = self._get_cdn_sub_folder(channel)
            return_value = "resource://%s/%s/%s" % (self.__resource_add_on, cdn_folder, file_name)

        self._logger.debug("Resolved texture '%s' to '%s'", file_name, return_value)
        return return_value

    def purge_texture_cache(self, channel):
        TextureHandler.purge_texture_cache(self, channel)
