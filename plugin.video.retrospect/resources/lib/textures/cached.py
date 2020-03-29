# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import hashlib
import shutil
import os
import io

from resources.lib.backtothefuture import PY2
from resources.lib.helpers.jsonhelper import JsonHelper
from resources.lib.textures import TextureHandler


class Cached(TextureHandler):
    # we should keep track of which ones we already used in this session, so we can refetch it in a purge situation.
    __retrievedTexturePaths = []

    def __init__(self, cdn_url, cache_path, cache_uri, logger, uri_handler):
        """ Creates a Cached Texture handler

        @param cdn_url:          The URL of the CDN
        @param cache_path:       The os path of the profile for caching
        @param cache_uri:        The uri path (Kodi uri special:// ) for caching
        @param logger:          The Logger instance
        @param uri_handler:      The UriHandler instance

        """

        TextureHandler.__init__(self, logger)

        self.__cdnUrl = cdn_url
        if not self.__cdnUrl:
            self.__cdnUrl = "https://cdn.rieter.net/plugin.video.retrospect.cdn/"

        self.__channelTexturePath = os.path.join(cache_path, "textures")
        self.__channelTextureUri = "%s/%s" % (cache_uri, "textures")
        if not os.path.isdir(self.__channelTexturePath):
            os.makedirs(self.__channelTexturePath)

        self.__uriHandler = uri_handler

        self.__textureQueue = {}

    def get_texture_uri(self, channel, file_name):
        """ Gets the full URI for the image file. Depending on the type of textures handling, it might also cache
        the texture and return that path.

        @param file_name: the file name
        @param channel:  the channel

        @return: the texture path

        """

        if file_name is None or file_name == "":
            return file_name

        if file_name.startswith("http"):
            self._logger.trace("Not going to resolve http(s) texture: '%s'.", file_name)
            return file_name

        if os.path.isabs(file_name) or file_name.startswith(self.__channelTextureUri):
            self._logger.trace("Already cached texture found: '%s'", file_name)
            return file_name

        # Check if we already have the file
        cdn_folder = self._get_cdn_sub_folder(channel)
        texture_dir = os.path.join(self.__channelTexturePath, cdn_folder)
        if not os.path.isdir(texture_dir):
            os.makedirs(texture_dir)

        texture_path = os.path.join(self.__channelTexturePath, cdn_folder, file_name)
        texture_uri = "%s/%s/%s" % (self.__channelTextureUri, cdn_folder, file_name)

        if not os.path.isfile(texture_path):
            # Missing item. Fetch it
            local_path = os.path.join(channel.path, file_name)
            # if False:
            if os.path.isfile(local_path):
                self._logger.trace("Queueing texture '%s' for caching from '%s'", file_name, local_path)
                self.__textureQueue[local_path] = texture_path
            else:
                uri = "%s/%s/%s" % (self.__cdnUrl, cdn_folder, file_name)
                self._logger.trace("Queueing texture '%s' for caching from '%s'", file_name, uri)
                self.__textureQueue[uri] = texture_path

        self._logger.debug("Resolved cached texture for '%s' to '%s'", file_name, texture_uri)
        Cached.__retrievedTexturePaths.append(texture_path)
        return texture_uri

    def number_of_missing_textures(self):
        """ Indication whether or not textures need to be retrieved.

        @return: a boolean value
        """

        return len(self.__textureQueue)

    def fetch_textures(self, dialog_call_back=None):
        """ Fetches all the needed textures

        @param dialog_call_back:  Callback method with signature
                                  Function(self, retrieved, total, perc, completed, status)

        @return: the number of bytes fetched

        """

        if len(self.__textureQueue) == 0:
            return

        self._logger.info("Fetching missing textures.")

        bytes_transferred = 0
        textures_total = len(self.__textureQueue)
        textures_completed = 0

        for uri, texture_path in self.__textureQueue.items():
            self._logger.debug("Fetching texture for '%s' to '%s'", uri, texture_path)
            if os.path.isfile(uri):
                shutil.copyfile(uri, texture_path)
            else:
                bytes_transferred += self.__fetch_texture(uri, texture_path)
            textures_completed += 1
            file_name = os.path.split(texture_path)[-1]

            if dialog_call_back(
                    textures_completed,
                    textures_total,
                    100 * textures_completed // textures_total,
                    False,
                    file_name):
                self._logger.warning("Texture retrieval cancelled")
                break

        return bytes_transferred

    def purge_texture_cache(self, channel):
        """ Removes those entries from the textures cache that are no longer required.

        @param channel:  the channel

        """

        self._logger.info("Purging Texture for: %s", channel.path)

        # read the md5 hashes
        with io.open(os.path.join(channel.path, "..", "channelpack.json"), 'rt', encoding='utf-8') as fd:
            lines = fd.read()

        textures = JsonHelper(lines).get_value("textures")

        # remove items not in the textures.md5
        cdn_folder = self._get_cdn_sub_folder(channel)
        texture_path = os.path.join(self.__channelTexturePath, cdn_folder)
        if not os.path.isdir(texture_path):
            self._logger.warning("Missing path '%s' to purge", texture_path)
            return

        images = [image for image in os.listdir(texture_path)
                  if image.lower().endswith(".png") or image.lower().endswith(".jpg")]

        texture_change = False

        for image in images:
            image_key = "%s/%s" % (cdn_folder, image)
            file_path = os.path.join(self.__channelTexturePath, cdn_folder, image)

            if image_key in textures:
                # verify the MD5 in the textures.md5
                md5 = self.__get_hash(file_path)
                if md5 == textures[image_key]:
                    self._logger.trace("Texture up to date: %s", file_path)
                else:
                    self._logger.warning("Texture expired: %s", file_path)
                    os.remove(file_path)
                    texture_change = True

                    # and fetch the updated one if it was already used
                    if file_path in Cached.__retrievedTexturePaths:
                        self.get_texture_uri(channel, image)
            else:
                self._logger.warning("Texture no longer required: %s", file_path)
                os.remove(file_path)
                texture_change = True

        # always reset the Kodi Texture cache for this channel
        if texture_change:
            self._purge_kodi_cache(cdn_folder)

        return

    def is_texture_or_empty(self, uri):
        """ Returns whether the uri points to a local resource or remote

        :param str uri: The URI for the texture

        :returns: Indicator whether or not the resource is local
        :rtype: bool

        """

        if not uri:
            return True

        return uri.startswith("special://")

    def __fetch_texture(self, uri, texture_path):
        """ Fetches a texture

        @param uri:         string - The uri to fetch from
        @param texture_path: string - The path to store to

        """

        image_bytes = self.__uriHandler.open(uri, no_cache=True)
        if image_bytes:
            with io.open(texture_path, mode='wb') as fs:
                if isinstance(image_bytes, bytes):
                    fs.write(image_bytes)
                else:
                    fs.write(image_bytes.encode())

            self._logger.debug("Retrieved texture: %s", uri)
        else:
            # fallback to local cache.
            # texturePath = os.path.join(self._channelPath, fileName)
            # self._logger.Error("Could not update Texture: %s. Falling back to: %s", uri, texturePath)
            self._logger.error("Could not update Texture:\nSource: '%s'\nTarget: '%s'", uri, texture_path)
        return len(image_bytes or [])

    def __get_hash(self, file_path):
        """ Returns the hash for the given file

        @param file_path: string - The file to generate a hash from

        @return: MD5 has for the file

        """

        hash_object = hashlib.md5()
        with open(file_path, "rb") as fs:
            for block in iter(lambda: fs.read(65536), "" if PY2 else b""):
                hash_object.update(block)
        md5 = hash_object.hexdigest()
        return md5
