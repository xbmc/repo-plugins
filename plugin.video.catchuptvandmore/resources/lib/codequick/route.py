# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
from collections import defaultdict
import logging
import inspect
import re

# Kodi imports
import xbmcplugin

# Package imports
from resources.lib.codequick.script import Script
from resources.lib.codequick.support import logger_id, auto_sort
from resources.lib.codequick.utils import ensure_native_str

__all__ = ["Route", "validate_listitems"]
_UNSET = object()

# Logger specific to this module
logger = logging.getLogger("%s.route" % logger_id)

# Localized string Constants
SELECT_PLAYBACK_ITEM = 25006
NO_DATA = 33077


def validate_listitems(raw_listitems):
    """Check if listitems are valid"""

    # Convert a generator of listitem into a list of listitems
    if inspect.isgenerator(raw_listitems):
        raw_listitems = list(raw_listitems)
    # Silently ignore False values
    elif raw_listitems is False:
        return False

    if raw_listitems:
        if isinstance(raw_listitems, (list, tuple)):
            if len(raw_listitems) == 1 and raw_listitems[0] is False:
                return False
            else:
                return raw_listitems
        else:
            raise ValueError("Unexpected return object: {}".format(type(raw_listitems)))
    else:
        raise RuntimeError("No items found")


class Route(Script):
    """
    This class is used to create "Route" callbacks. “Route" callbacks, are callbacks that
    return "listitems" which will show up as folders in Kodi.

    Route inherits all methods and attributes from :class:`codequick.Script<codequick.script.Script>`.

    The possible return types from Route Callbacks are.
        * ``iterable``: "List" or "tuple", consisting of :class:`codequick.listitem<codequick.listing.Listitem>` objects.
        * ``generator``: A Python "generator" that return's :class:`codequick.listitem<codequick.listing.Listitem>` objects.
        * ``False``: This will cause the "plugin call" to quit silently, without raising a RuntimeError.

    :raises RuntimeError: If no content was returned from callback.

    :example:
        >>> from resources.lib.codequick import Route, Listitem
        >>>
        >>> @Route.register
        >>> def root(_):
        >>>     yield Listitem.from_dict("Extra videos", subfolder)
        >>>     yield Listitem.from_dict("Play video",
        >>>           "http://www.example.com/video1.mkv")
        >>>
        >>> @Route.register
        >>> def subfolder(_):
        >>>     yield Listitem.from_dict("Play extra video",
        >>>           "http://www.example.com/video2.mkv")
    """

    # Change listitem type to 'folder'
    is_folder = True

    def __init__(self):
        super(Route, self).__init__()
        self.update_listing = self.params.get(u"_updatelisting_", False)
        self.category = re.sub(u"\(\d+\)$", u"", self._title).strip()
        self.cache_to_disc = self.params.get(u"_cache_to_disc_", True)
        self.redirect_single_item = False
        self._manual_sort = list()
        self.content_type = _UNSET
        self.autosort = True

    def _process_results(self, raw_listitems):
        """Handle the processing of the listitems."""
        raw_listitems = validate_listitems(raw_listitems)
        if raw_listitems is False:
            xbmcplugin.endOfDirectory(self.handle, False)
            return None

        # Create a new list containing tuples, consisting of path, listitem, isfolder.
        listitems = []
        folder_counter = 0.0
        mediatypes = defaultdict(int)
        for listitem in raw_listitems:
            if listitem:  # pragma: no branch
                # noinspection PyProtectedMember
                listitem_tuple = listitem._close()
                listitems.append(listitem_tuple)
                if listitem_tuple[2]:  # pragma: no branch
                    folder_counter += 1

                if "mediatype" in listitem.info:
                    mediatypes[listitem.info["mediatype"]] += 1

        # If redirect_single_item is set to True then redirect view to the first
        # listitem if it's the only listitem and that listitem is a folder
        if self.redirect_single_item and len(listitems) == 1 and listitems[0][2] is True:
            return listitems[0][0]  # return the listitem path

        # Guess if this directory listing is primarily a folder or video listing.
        # Listings will be considered to be a folder if more that half the listitems are folder items.
        isfolder = folder_counter > (len(listitems) / 2)

        # Sets the category for skins to display modes.
        xbmcplugin.setPluginCategory(self.handle, ensure_native_str(self.category))

        if self.content_type is not None:
            self.__content_type("files" if isfolder else "videos", mediatypes)

        # Add sort methods only if not a folder(Video listing)
        if not isfolder:
            self.__add_sort_methods(self._manual_sort)

        # Pass the listitems and relevant data to kodi
        success = xbmcplugin.addDirectoryItems(self.handle, listitems, len(listitems))
        xbmcplugin.endOfDirectory(self.handle, success, self.update_listing, self.cache_to_disc)

    def __content_type(self, default_type, mediatypes):  # type: (str, defaultdict) -> None
        """Configure plugin properties, content, category and sort methods."""

        # See if we can guess the content_type based on the mediatypes from the listitem
        if mediatypes and self.content_type is _UNSET:
            if len(mediatypes) > 1:
                from operator import itemgetter
                # Sort mediatypes by there count, and return the highest count mediatype
                mediatype = sorted(mediatypes.items(), key=itemgetter(1))[-1][0]
            else:
                mediatype = mediatypes.popitem()[0]

            # Convert mediatype to a content_type, not all mediatypes can be converted directly
            if mediatype in ("video", "movie", "tvshow", "episode", "musicvideo", "song", "album", "artist"):
                self.content_type = mediatype + "s"

        # Set the add-on content type
        content_type = self.content_type if self.content_type and self.content_type is not _UNSET else default_type
        xbmcplugin.setContent(self.handle, content_type)
        logger.debug("Content-type: %s", content_type)

    def __add_sort_methods(self, sortmethods):  # type: (list) -> None
        """Add sort methods to kodi."""
        _addSortMethod = xbmcplugin.addSortMethod

        if self.autosort:
            # Add unsorted sort method if not sorted by date and no manually set sortmethods are given
            if auto_sort and not (sortmethods or xbmcplugin.SORT_METHOD_DATE in auto_sort):
                sortmethods.append(xbmcplugin.SORT_METHOD_UNSORTED)

            # Keep the order of the manually set sort methods
            # Only sort the auto sort methods
            for method in sorted(auto_sort):
                if method not in sortmethods:
                    sortmethods.append(method)

        if sortmethods:
            for sortMethod in sortmethods:
                _addSortMethod(self.handle, sortMethod)
        else:
            # If no sortmethods are given then set sort mehtod to unsorted
            _addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)

    def add_sort_methods(self, *methods, **kwargs):
        """
        Add sorting method(s).

        Any number of sort method's can be given as multiple arguments.
        Normally this should not be needed, as sort method's are auto detected.

        You can pass an optional keyword only argument, 'disable_autosort' to disable auto sorting.

        :param int methods: One or more Kodi sort method's.

        .. seealso:: The full list of sort methods can be found at.\n
                     https://codedocs.xyz/xbmc/xbmc/group__python__xbmcplugin.html#ga85b3bff796fd644fb28f87b136025f40
        """
        # Disable autosort if requested
        if kwargs.get("disable_autosort", False):
            self.autosort = False

        # Can't use sets here as sets don't keep order
        for method in methods:
            self._manual_sort.append(method)
