# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

from textures import TextureHandler


class Remote(TextureHandler):
    def __init__(self, cdn_url, logger):
        TextureHandler.__init__(self, logger)

        self.__cdnUrl = cdn_url
        if not self.__cdnUrl:
            self.__cdnUrl = "https://cdn.rieter.net/plugin.video.retrospect.cdn/"

    def purge_texture_cache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        @param channel:  the channel

        """

        cdn_folder = self._get_cdn_sub_folder(channel)
        self._logger.info("Purging Kodi Texture for: %s", cdn_folder)
        self._purge_kodi_cache(cdn_folder)
        return

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
        else:
            cdn_folder = self._get_cdn_sub_folder(channel)
            return_value = "%s/%s/%s" % (self.__cdnUrl, cdn_folder, file_name)

        self._logger.debug("Resolved texture '%s' to '%s'", file_name, return_value)
        return return_value
