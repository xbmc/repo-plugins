# SPDX-License-Identifier: GPL-3.0-or-later

import pickle
import os
import io
import sys
import base64
from functools import reduce
from typing import List, Tuple, Dict

from resources.lib.regexer import Regexer
from resources.lib.logger import Logger
from resources.lib.mediaitem import MediaItem


class Pickler:
    # hack for Base64 chars that are URL encoded. We only need 3 (or 6 to make it case-insensitive)
    # and then we don't need to use urlencode which is slow in Python.
    __Base64CharsDecode = {
        "-": "\n",
        "%3d": "=",
        "%3D": "=",
        "%2f": "/",
        "%2F": "/",
        "%2b": "+",
        "%2B": "+"
    }
    __Base64CharsEncode = {
        "\n": "-",
        "=": "%3d",
        "/": "%2f",
        "+": "%2b",
    }

    __store_separator = "--"

    def __init__(self, pickle_store_path=None):
        # store some vars for speed optimization
        self.__pickle_container = dict()  # : storage for pickled items to prevent duplicate pickling
        self.__depickle_container = dict()  # : storage for depickled items.

        self.__pickle_store_path: str = pickle_store_path
        self.__compress = True
        if self.__compress:
            self.__ext = "store.z"
        else:
            self.__ext = "store"

    def de_pickle_child_items(self, hex_string: str) -> Tuple[str, Dict[str, List[MediaItem]]]:
        """ De-serializes a serialized mediaitem.

        Warning: Pickling from Python2 to Python3 will not work.

        :param hex_string: Base64 encoded string that should be decoded.

        :return: The object that was Pickled and Base64 encoded.
        """

        if not self.is_pickle_store_id(hex_string):
            raise ValueError("Cannot fetch child items for non-store item.")

        store_guid, item_guid = hex_string.split(Pickler.__store_separator)
        return store_guid, self.__retrieve_media_items_from_store(store_guid)

    def de_pickle_media_item(self, hex_string: str) -> MediaItem:
        """ De-serializes a serialized mediaitem.

        Warning: Pickling from Python2 to Python3 will not work.

        :param hex_string: Base64 encoded string that should be decoded.

        :return: The object that was Pickled and Base64 encoded.

        """

        if self.is_pickle_store_id(hex_string):
            return self.__retrieve_media_item_from_store(hex_string)

        # In order to not break any already pickled objects, we need to make sure that we have
        if "mediaitem" not in sys.modules:
            import resources.lib.mediaitem
            sys.modules['mediaitem'] = resources.lib.mediaitem

        hex_string = hex_string.rstrip(' ')
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsDecode[y]),
                            Pickler.__Base64CharsDecode.keys(),
                            hex_string)

        Logger.trace("DePickle: HexString: %s (might be truncated)", hex_string[0:256])

        pickle_string = base64.b64decode(hex_string)  # type: bytes
        pickle_item = pickle.loads(pickle_string)  # type: MediaItem
        return pickle_item

    def pickle_media_item(self, item: MediaItem) -> str:
        """ Serialises a mediaitem using Pickle

        :param item: The item that should be serialised

        :return: A pickled and Base64 encoded serialization of the `item`.

        """

        if item.guid in self.__pickle_container:
            Logger.trace("Pickle Container cache hit: %s", item.guid)
            return self.__pickle_container[item.guid]

        pickle_string = pickle.dumps(item, protocol=pickle.HIGHEST_PROTOCOL)  # type: bytes
        hex_bytes = base64.b64encode(pickle_string)  # type: bytes
        hex_string = hex_bytes.decode()  # type: str

        # if not unquoted, we must replace the \n's for the URL
        hex_string = reduce(lambda x, y: x.replace(y, Pickler.__Base64CharsEncode[y]),
                            Pickler.__Base64CharsEncode.keys(),
                            hex_string)

        self.__pickle_container[item.guid] = hex_string
        return hex_string

    def purge_store(self, addon_id: str, age: int = 30):
        """ Purges all files older than xx days.

        :param str addon_id: The ID of this add-on
        :param int age:      The age (in days) for pickles to be purged

        """

        if self.__pickle_store_path is None:
            return

        Logger.info("PickleStore: Purging store items older than %d days", age)

        # Retrieve the store_id's for the favourites
        favourite_pickle_stores = self.__get_kodi_favourites(addon_id)

        # Local imports to increase speed
        import glob
        import time

        pickles_path = os.path.join(
            self.__pickle_store_path, "pickles", "*", "*", "*.{}".format(self.__ext))

        cache_time = age * 24 * 60 * 60
        for filename in glob.glob(pickles_path):
            create_time = os.path.getctime(filename)
            pickle_store_id = os.path.split(filename)[1].split(".", 1)[0]
            if create_time + cache_time < time.time():
                if pickle_store_id in favourite_pickle_stores:
                    Logger.debug("PickleStore: Advanced cleaning of favourite '%s'", filename)
                    pickle_favs = favourite_pickle_stores[pickle_store_id]

                    # Clear all but the favourites.
                    pickles_dir, pickles_path = self.__get_pickle_path(pickle_store_id)

                    # Update the content and save it.
                    content = self.__load_pickle_store_file(pickles_path)
                    store_children: dict = content["children"]
                    content["favourites"] = pickle_favs
                    content["children"] = {k: v for k, v in store_children.items() if k in pickle_favs}
                    self.__save_pickle_store_file(content, pickles_path)

                    Logger.debug(
                        "PickleStore Clean Result: %d children, %d favourites",
                        len(content["children"]),
                        len(content.get("favourites", []))
                    )
                    continue

                os.remove(filename)
                Logger.debug("PickleStore: Removed file '%s'", filename)

    def store_media_items(self, store_guid: str, parent: MediaItem, children: List[MediaItem]) -> None:
        """ Store the MediaItems in the given store path

        :param store_guid:  The guid used for storage
        :param parent:      The parent item
        :param children:    The child items

        """

        if self.__pickle_store_path is None:
            raise ValueError("Cannot find pickle store path")

        if store_guid is None:
            raise ValueError("No parent and not channel guid specified")

        children = children or []

        # The path is constructed like this for abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx:
        # <storepath>/ab/cd/abcdef01-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        pickles_dir, pickles_path = self.__get_pickle_path(store_guid)
        Logger.debug("PickleStore: Write to '%s'", pickles_path)

        if not os.path.isdir(pickles_dir):
            os.makedirs(pickles_dir)

        current_content = {
            "parent": parent,
            "children": {item.guid: item for item in children}
        }

        # If there was previous content create a combined list, but keep
        # track of the favourite items' GUIDs.
        if os.path.isfile(pickles_path):
            Logger.debug("PickleStore: Merging '%s'", pickles_path)
            prevous_content = self.__load_pickle_store_file(pickles_path) or {}
            prev_children = prevous_content.get("children", {})
            if prev_children:
                # Combine the previous children and update it with the new ones as
                # we always want to keep the most recent ones.
                prev_children.update(current_content["children"])
                current_content["children"] = prev_children

            # ...and copy the favourites.
            favourites = prevous_content.get("favourites", {})
            if favourites:
                current_content["favourites"] = favourites

            Logger.debug(
                "PickleStore: Merged into %d children, %d favourites",
                len(current_content["children"]),
                len(current_content.get("favourites", []))
            )

        self.__save_pickle_store_file(current_content, pickles_path)

    def is_pickle_store_id(self, pickle):
        """ Checks if a Pickle string is an actual pickle or a reference to a PickleStore entry

        :param str pickle:  The Pickle value.

        :return: Indicator if the pickle is a referece to a PickleStore
        :rtype: bool
        """
        return self.__store_separator in pickle

    def __retrieve_media_items_from_store(self, store_guid):
        content = self.__depickle_container.get(store_guid)
        if content:
            items = content.get("children")
            return items

        pickles_dir, pickles_path = self.__get_pickle_path(store_guid)
        content = self.__load_pickle_store_file(pickles_path)
        if not content:
            return None

        items = content.get("children")
        self.__depickle_container[store_guid] = content
        return items

    def __retrieve_media_item_from_store(self, storage_location: str) -> MediaItem:
        store_guid, item_guid = storage_location.split(Pickler.__store_separator)
        items = self.__retrieve_media_items_from_store(store_guid)

        item_pickle = items.get(item_guid)
        return item_pickle

    def __get_pickle_path(self, store_guid) -> Tuple[str, str]:
        # file storage is always lower case
        store_guid = store_guid.lower()
        pickles_file = "{}.{}".format(store_guid, self.__ext)

        pickles_dir = os.path.join(
            self.__pickle_store_path, "pickles", store_guid[0:2], store_guid[2:4])
        pickles_path = os.path.join(pickles_dir, pickles_file)
        return pickles_dir, pickles_path

    def __get_kodi_favourites(self, addon_id: str) -> Dict[str, List[str]]:
        """ Retrieves the PickleStore ID's corresponding to Kodi Favourites using the json RPC

        :return: A set of PickleStore ID's
        :rtype: set(str)

        """

        import json
        import xbmc

        # Use a set() for performance
        favourite_pickle_stores = dict()

        # Do the RPC
        req = {
            "jsonrpc": "2.0",
            "method": "Favourites.GetFavourites",
            "params": {
                "type": None,
                "properties": ["path", "windowparameter"]
            },
            "id": 1
        }
        rpc_result = xbmc.executeJSONRPC(json.dumps(req))
        Logger.trace("PickleStore: Received favourites '%s'", rpc_result)
        rpc_result_data = json.loads(rpc_result)
        favourites = rpc_result_data.get("result", {}).get("favourites")
        if not favourites:
            return favourite_pickle_stores

        # Start of the add-on url
        addon_url = "plugin://{}".format(addon_id)

        for fav in favourites:
            fav_name = fav.get("title", "")
            fav_path = fav.get("path", fav.get("windowparameter")) or ""
            if not fav_path.startswith(addon_url):
                continue

            # Is it a favourite with a PickleStore ID?
            pickle_match = Regexer.do_regex(
                r"pickle=([^&]+){}([^&]+)".format(Pickler.__store_separator), fav_path)
            if not pickle_match:
                continue

            pickle_store_id, pickle_id = pickle_match[0]

            Logger.debug("PickleStore: Found favourite: %s (%s)", fav_name, fav_path)

            if pickle_store_id.lower() in favourite_pickle_stores:
                favourite_pickle_stores[pickle_store_id.lower()].append(pickle_id)
            else:
                favourite_pickle_stores[pickle_store_id.lower()] = [pickle_id]

        return favourite_pickle_stores

    def __save_pickle_store_file(self, current_content: dict, pickles_path: str):
        Logger.debug("PickleStore: Storing items into '%s'", pickles_path)
        if self.__compress:
            pickle_content = pickle.dumps(current_content, protocol=pickle.HIGHEST_PROTOCOL)
            import zlib
            with io.open(pickles_path, 'wb+') as fp:
                fp.write(zlib.compress(pickle_content, zlib.Z_BEST_COMPRESSION))
        else:
            with io.open(pickles_path, "wb+") as fp:
                pickle.dump(current_content, fp, protocol=pickle.HIGHEST_PROTOCOL)

    def __load_pickle_store_file(self, pickles_path: str):
        Logger.debug("PickleStore: Reading items from '%s'", pickles_path)
        try:
            if self.__compress:
                import zlib
                with io.open(pickles_path, 'rb') as fp:
                    pickle_bytes = zlib.decompress(fp.read())
                    content = pickle.loads(pickle_bytes)
            else:
                with io.open(pickles_path, "rb") as fp:
                    content = pickle.load(fp)
        except:
            Logger.error("Error opening '%s'", pickles_path, exc_info=True)
            return None

        return content
