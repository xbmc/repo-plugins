#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

import os

from textures import TextureHandler


class Local(TextureHandler):
    def __init__(self, logger):
        TextureHandler.__init__(self, logger)

    def get_texture_uri(self, channel, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param file_name: the file name
        @param channel:  the channel

        """

        if file_name is None or file_name == "":
            return file_name

        if file_name.startswith("http"):
            self._logger.trace("Not going to resolve http(s) texture: '%s'.", file_name)
            return file_name

        if os.path.isabs(file_name):
            return_value = file_name
        else:
            return_value = os.path.join(channel.path, file_name)

        self._logger.trace("Resolved texture '%s' to '%s'", file_name, return_value)
        return return_value
