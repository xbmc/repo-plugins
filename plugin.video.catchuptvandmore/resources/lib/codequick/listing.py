# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
from time import strptime, strftime
import logging
import os
import re

# Fix attemp for
import _strptime

# Kodi imports
import xbmcplugin
import xbmcgui

# Package imports
from resources.lib.codequick.script import Script
from resources.lib.codequick.support import auto_sort, build_path, logger_id, dispatcher
from resources.lib.codequick.utils import ensure_unicode, ensure_native_str, unicode_type, PY3, bold

if PY3:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections.abc import MutableMapping, MutableSequence
else:
    # noinspection PyUnresolvedReferences, PyCompatibility
    from collections import MutableMapping, MutableSequence

__all__ = ["Listitem"]

# Logger specific to this module
logger = logging.getLogger("%s.listitem" % logger_id)

# Listitem thumbnail locations
local_image = ensure_native_str(os.path.join(Script.get_info("path"), u"resources", u"media", u"{}"))
# FIX FOR LOCAL USAGE
# global_image = ensure_native_str(os.path.join(Script.get_info("path_global"), u"resources", u"media", u"{}"))
global_image = ensure_native_str(os.path.join(Script.get_info("path_global"), u"resources", u"media", u"codequick", u"{}"))

# Prefetch fanart/icon for use later
_fanart = Script.get_info("fanart")
fanart = ensure_native_str(_fanart) if os.path.exists(_fanart) else None
icon = ensure_native_str(Script.get_info("icon"))

# Stream type map to ensure proper stream value types
stream_type_map = {"duration": int,
                   "channels": int,
                   "aspect": float,
                   "height": int,
                   "width": int}

# Listing sort methods & sort mappings.
# Skips infolables that have no sortmethod and type is string. As by default they will be string anyway
# noinspection PyUnresolvedReferences
infolable_map = {"artist": (None, xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE),
                 "studio": (ensure_native_str, xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE),
                 "title": (ensure_native_str, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE),
                 "album": (ensure_native_str, xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE),
                 "code": (ensure_native_str, xbmcplugin.SORT_METHOD_PRODUCTIONCODE),
                 "count": (int, xbmcplugin.SORT_METHOD_PROGRAM_COUNT),
                 "rating": (float, xbmcplugin.SORT_METHOD_VIDEO_RATING),
                 "mpaa": (ensure_native_str, xbmcplugin.SORT_METHOD_MPAA_RATING),
                 "year": (int, xbmcplugin.SORT_METHOD_VIDEO_YEAR),
                 "listeners": (int, xbmcplugin.SORT_METHOD_LISTENERS),
                 "tracknumber": (int, xbmcplugin.SORT_METHOD_TRACKNUM),
                 "episode": (int, xbmcplugin.SORT_METHOD_EPISODE),
                 "country": (ensure_native_str, xbmcplugin.SORT_METHOD_COUNTRY),
                 "genre": (None, xbmcplugin.SORT_METHOD_GENRE),
                 "date": (ensure_native_str, xbmcplugin.SORT_METHOD_DATE),
                 "size": (int if PY3 else long, xbmcplugin.SORT_METHOD_SIZE),
                 "sortepisode": (int, None),
                 "sortseason": (int, None),
                 "userrating": (int, None),
                 "discnumber": (int, None),
                 "playcount": (int, None),
                 "overlay": (int, None),
                 "season": (int, None),
                 "top250": (int, None),
                 "setid": (int, None),
                 "dbid": (int, None)}

# Convenient function for adding to autosort set
auto_sort_add = auto_sort.add

# Map quality values to it's related video resolution, used by 'strea.hd'
quality_map = ((768, 576), (1280, 720), (1920, 1080), (3840, 2160))  # SD, 720p, 1080p, 4K

# Re.sub to remove formatting from label strings
strip_formatting = re.compile(r"\[[^\]]+?\]").sub

# Localized string Constants
RELATED_VIDEOS = 32201
RECENT_VIDEOS = 32002
RECENT_VIDEOS_PLOT = 32004
ALLVIDEOS = 32003
NEXT_PAGE = 33078
NEXT_PAGE_PLOT = 32005
SEARCH_PLOT = 32006
SEARCH = 137


class Params(MutableMapping):
    def __init__(self):
        self.raw_dict = {}

    def __getitem__(self, key):
        value = self.raw_dict[key]
        return value.decode("utf8") if isinstance(value, bytes) else value

    def __setitem__(self, key, value):
        if isinstance(value, bytes):
            self.raw_dict[key] = value.decode("utf8")
        else:
            self.raw_dict[key] = value

    def __delitem__(self, key):  # type: (str) -> None
        del self.raw_dict[key]

    def __contains__(self, key):  # type: (str) -> bool
        return key in self.raw_dict

    def __len__(self):
        return len(self.raw_dict)

    def __iter__(self):
        return iter(self.raw_dict)

    def __str__(self):
        return str(self.raw_dict)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.raw_dict)

    def clean(self):
        """Remove any and all None values from the dictionary."""
        for key in [key for key, val in self.raw_dict.items() if not val]:
            del self.raw_dict[key]


class Art(Params):
    """
    Dictionary like object, that allows you to add various images. e.g. "thumb", "fanart".

    if "thumb", "fanart" or "icon"  is not set, then they will be set automaticly based on the add-on's
    fanart and icon images.

    .. note::

        The automatic image values can be disabled by setting an empty string. e.g. item.art["thumb"] = "".

    .. note::

        This class inherits all methods and attributes from :class:`collections.MutableMapping`.

    Expected art values are.
        * thumb
        * poster
        * banner
        * fanart
        * clearart
        * clearlogo
        * landscape
        * icon

    :example:
        >>> item = Listitem()
        >>> item.art["icon"] = "http://www.example.ie/icon.png"
        >>> item.art["fanart"] = "http://www.example.ie/fanart.jpg"
        >>> item.art.local_thumb("thumbnail.png")
    """

    def __init__(self, listitem):  # type: (xbmcgui.ListItem) -> None
        super(Art, self).__init__()
        self._listitem = listitem

    def __setitem__(self, key, value):  # type: (str, str) -> None
        self.raw_dict[key] = ensure_native_str(value)

    def local_thumb(self, image):
        """
        Set the "thumbnail" image to a image file, located in the add-on "resources/media" directory.

        :param str image: Filename of the image.
        """
        # Here we can't be sure if 'image' only contains ascii characters, so ensure_native_str is needed
        self.raw_dict["thumb"] = local_image.format(ensure_native_str(image))

    def global_thumb(self, image):
        """
        Set the "thumbnail" image to a image file, located in the codequick "resources/media" directory.

        The available global thumbnail images are.
            * next.png        - Arrow pointing to the right.
            * videos.png      - Circle with a play button in the middle.
            * search.png      - An image of a magnifying glass.
            * search_new.png  - A magnifying glass with plus symbol in the middle.
            * playlist.png    - Image of three bulleted lines.
            * recent.png      - Image of a clock.

        :param str image: Filename of the image.
        """
        # Here we know that 'image' should only contain ascii characters
        # So there is no neeed to use ensure_native_str
        self.raw_dict["thumb"] = global_image.format(image)

    def _close(self, isfolder):
        if fanart and "fanart" not in self.raw_dict:  # pragma: no branch
            self.raw_dict["fanart"] = fanart
        if "thumb" not in self.raw_dict:  # pragma: no branch
            self.raw_dict["thumb"] = icon
        if "icon" not in self.raw_dict:  # pragma: no branch
            self.raw_dict["icon"] = "DefaultFolder.png" if isfolder else "DefaultVideo.png"

        self.clean()  # Remove all None values
        self._listitem.setArt(self.raw_dict)


class Info(Params):
    """
    Dictionary like object, that allow’s you to add listitem "infoLabels".

    "InfoLabels" are like metadata for listitems. e.g. "duration", "genre", "size", "rating" and or "plot".
    They are also used for sorting purpose's, sort methods will be automatically selected.

    Some "infolabels" need to be of a given type e.g. "size" as "long", "rating" as "float".
    For the most part, this conversion will be done automatically.

    Example of what would happen is.
        * "duration" would be converted to ``int`` and "xbmcplugin.SORT_METHOD_VIDEO_RUNTIME"
          sort method will be selected.
        * "size" would be converted to ``long`` and "xbmcplugin.SORT_METHOD_SIZE"
          sort method will be selected.

    .. seealso:: The full list of listitem "infoLabels" can be found at:

        https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14

    .. note:: Duration infolabel value can be either in "seconds" or as a "hh:mm:ss" string.

    This class inherits all methods and attributes from :class:`collections.MutableMapping`.

    :examples:
        >>> item = Listitem()
        >>> item.info['genre'] = 'Science Fiction'
        >>> item.info['size'] = 256816
    """

    def __init__(self, listitem):  # type: (xbmcgui.ListItem) -> None
        super(Info, self).__init__()
        self._listitem = listitem

    def __setitem__(self, key, value):
        if value is None or value == "":
            logger.debug("Ignoring empty infolable: '%s'", key)
            return None

        # Convert duration into an integer
        elif key == "duration":
            auto_sort_add(xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
            self.raw_dict[key] = self._duration(value)
        else:
            # The sort method to set and the type that the infolabel should be
            type_converter, sort_type = infolable_map.get(key, (None, None))

            # Convert value to required type needed for this infolabel
            if type_converter:
                try:
                    value = type_converter(value)
                except ValueError:
                    msg = "value of '%s' for infolabel '%s', is not of type '%s'"
                    raise TypeError(msg % (value, key, type_converter))
                else:
                    self.raw_dict[key] = value

            elif isinstance(value, str):
                self.raw_dict[key] = value
            elif isinstance(value, unicode_type):
                # Only executes on python 2
                self.raw_dict[key] = value.encode("utf8")
            elif isinstance(value, bytes):
                # Only executes on python 3
                self.raw_dict[key] = value.decode("utf8")
            else:
                self.raw_dict[key] = value

            if sort_type:
                # Set the associated sort method for this infolabel
                auto_sort_add(sort_type)

    def date(self, date, date_format):
        """
        Set the date infolabel.

        :param str date: The date for the listitem.
        :param str date_format: The format of the date as a strftime directive e.g. "june 27, 2017" => "%B %d, %Y"

        .. seealso:: The full list of directives can be found at:

                    https://docs.python.org/3.6/library/time.html#time.strftime

        :example:
            >>> item = Listitem()
            >>> item.info.date('june 27, 2017', '%B %d, %Y')
        """
        converted_date = strptime(ensure_native_str(date), date_format)
        self.raw_dict["date"] = strftime("%d.%m.%Y", converted_date)  # 27.06.2017
        self.raw_dict["aired"] = strftime("%Y-%m-%d", converted_date)  # 2017-06-27
        self.raw_dict["year"] = strftime("%Y", converted_date)  # 2017
        auto_sort_add(xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        auto_sort_add(xbmcplugin.SORT_METHOD_DATE)

    @staticmethod
    def _duration(duration):
        """Converts duration from a string of 'hh:mm:ss' into seconds."""
        if isinstance(duration, (str, unicode_type)):
            duration = duration.strip(";").strip(":")
            if ":" in duration or ";" in duration:
                # Split Time By Marker and Convert to Integer
                time_parts = duration.replace(";", ":").split(":")
                time_parts.reverse()
                duration = 0
                counter = 1

                # Multiply Each 'Time Delta' Segment by it's Seconds Equivalent
                for part in time_parts:
                    duration += int(part) * counter
                    counter *= 60
            else:
                # Convert to Interger
                duration = int(duration)

        return duration

    def _close(self, content_type):
        raw_dict = self.raw_dict
        # Add label as plot if no plot is found
        if "plot" not in raw_dict:  # pragma: no branch
            raw_dict["plot"] = raw_dict["title"]

        self._listitem.setInfo(content_type, raw_dict)


class Property(Params):
    def __init__(self, listitem):  # type: (xbmcgui.ListItem) -> None
        super(Property, self).__init__()
        self._listitem = listitem

    def __setitem__(self, key, value):  # type: (str, str) -> None
        if value:
            self.raw_dict[key] = ensure_unicode(value)
        else:
            logger.debug("Ignoring empty property: '%s'", key)

    def _close(self):
        for key, value in self.raw_dict.items():
            self._listitem.setProperty(key, value)


class Stream(Params):
    """
    Dictionary like object, that allows you to add "stream details". e.g. "video_codec", "audio_codec".

    Expected stream values are.
        * video_codec        - str (h264)
        * aspect             - float (1.78)
        * width              - integer (1280)
        * height             - integer (720)
        * channels           - integer (2)
        * audio_codec        - str (AAC)
        * audio_language     - str (en)
        * subtitle_language  - str (en)

    Type convertion will be done automatically, so manual convertion is not required.

    This class inherits all methods and attributes from :class:`collections.MutableMapping`.

    :example:
        >>> item = Listitem()
        >>> item.stream['video_codec'] = 'h264'
        >>> item.stream['audio_codec'] = 'aac'
    """

    def __init__(self, listitem):  # type: (xbmcgui.ListItem) -> None
        super(Stream, self).__init__()
        self._listitem = listitem

    def __setitem__(self, key, value):
        if not value:
            logger.debug("Ignoring empty stream detail value for: '%s'", key)
            return None

        # Ensure that value is of required type
        type_converter = stream_type_map.get(key, ensure_native_str)
        try:
            value = type_converter(value)
        except ValueError:
            msg = "Value of '%s' for stream info '%s', is not of type '%s'"
            raise TypeError(msg % (value, key, type_converter))
        else:
            self.raw_dict[key] = value

    def hd(self, quality, aspect=None):
        """
        Convenient method to set required stream info to show "SD/HD/4K" logos.

        The values witch are set are "width", "height" and "aspect".
        If no aspect ratio is given, then a ratio of 1.78(16:9) is set when the quality is 720p or greater.

        Quality options are.
            * 0 = 480p
            * 1 = 720p
            * 2 = 1080p
            * 3 = 4K.

        :type quality: int or None
        :param quality: Quality of the stream.
        :param float aspect: [opt] The "aspect ratio" of the video.

        :example:
            >>> item = Listitem()
            >>> item.stream.hd(2, aspect=1.78) # 1080p
        """
        # Skip if value is None(Unknown), useful when passing a variable with unkown value
        if quality is None:
            return None

        # Set video resolution
        try:
            self.raw_dict["width"], self.raw_dict["height"] = quality_map[quality]
        except IndexError:
            raise ValueError("quality id must be within range (0 to 3): '{}'".format(quality))

        # Set the aspect ratio if one is given
        if aspect:
            self["aspect"] = aspect

        # Or set the aspect ratio to 16:9 for HD content and above
        elif self.raw_dict["height"] >= 720:
            self.raw_dict["aspect"] = 1.78

    def _close(self):
        video = {}
        subtitle = {}
        audio = {"channels": 2}
        # Populate the above dictionary with the appropriate key/value pairs
        for key, value in self.raw_dict.items():
            rkey = key.split("_")[-1]
            if key in ("video_codec", "aspect", "width", "height", "duration"):
                video[rkey] = value
            elif key in ("audio_codec", "audio_language", "channels"):
                audio[rkey] = value
            elif key == "subtitle_language":
                subtitle[rkey] = value
            else:
                raise KeyError("unknown stream detail key: '{}'".format(key))

        # Now we are ready to send the stream info to kodi
        self._listitem.addStreamInfo("audio", audio)
        if video:
            self._listitem.addStreamInfo("video", video)
        if subtitle:
            self._listitem.addStreamInfo("subtitle", subtitle)


class Context(list):
    """
    Adds item(s) to the context menu of the listitem.

    This is a list containing "tuples" consisting of ("label", "command") pairs.

    This class inherits all methods and attributes from the build-in data type :class:`list`.

    .. seealso:: The full list of built-in functions can be found at:

                 http://kodi.wiki/view/List_of_Built_In_Functions
    """

    def __init__(self, listitem):  # type: (xbmcgui.ListItem) -> None
        super(Context, self).__init__()
        self._listitem = listitem

    def related(self, callback, *args, **kwargs):
        """
        Convenient method to add a "Related Videos" context menu item.

        All this really does is to call "context.container" and sets "label" for you.

        :param callback: The function that will be called when menu item is activated.
        :param args: [opt] "Positional" arguments that will be passed to the callback.
        :param kwargs: [opt] "Keyword" arguments that will be passed to the callback.
        """
        # Add '_updatelisting_ = True' to callback params if called from the same callback as is given here
        if callback.route == dispatcher.get_route():
            kwargs["_updatelisting_"] = True

        related_videos_text = Script.localize(RELATED_VIDEOS)
        kwargs["_title_"] = related_videos_text
        self.container(callback, related_videos_text, *args, **kwargs)

    def container(self, callback, label, *args, **kwargs):
        """
        Convenient method to add a context menu item that links to a "container".

        :type label: str
        :param callback: The function that will be called when menu item is activated.
        :param label: The label of the context menu item.
        :param args: [opt] "Positional" arguments that will be passed to the callback.
        :param kwargs: [opt] "Keyword" arguments that will be passed to the callback.
        """
        command = "XBMC.Container.Update(%s)" % build_path(callback, args, kwargs)
        self.append((label, command))

    def script(self, callback, label, *args, **kwargs):
        """
        Convenient method to add a context menu item that links to a "script".

        :param callback: The function that will be called when menu item is activated.
        :type label: str or unicode
        :param label: The label of the context menu item.
        :param args: [opt] "Positional" arguments that will be passed to the callback.
        :param kwargs: [opt] "Keyword" arguments that will be passed to the callback.
        """
        command = "XBMC.RunPlugin(%s)" % build_path(callback, args, kwargs)
        self.append((label, command))

    def _close(self):
        if self:
            self._listitem.addContextMenuItems(self)


class Listitem(object):
    """
    The “listitem” control is used for the creating "folder" or "video" items within Kodi.

    :param str content_type: [opt] Type of content been listed. e.g. "video", "music", "pictures".
    """

    def __init__(self, content_type="video"):
        self._content_type = content_type
        self.is_playable = True
        self.is_folder = False
        self._args = None
        self.path = ""

        #: The underlining kodi listitem object, for advanced use.
        self.listitem = listitem = xbmcgui.ListItem()

        #: List of paths to subtitle files.
        self.subtitles = []

        self.info = Info(listitem)
        """
        Dictionary like object for adding "infoLabels".
        See :class:`listing.Info<codequick.listing.Info>` for more details.
        """

        self.art = Art(listitem)
        """
        Dictionary like object for adding "listitem art".
        See :class:`listing.Art<codequick.listing.Art>` for more details.
        """

        self.stream = Stream(listitem)
        """
        Dictionary like object for adding "stream details".
        See :class:`listing.Stream<codequick.listing.Stream>` for more details.
        """

        self.context = Context(listitem)
        """
        List object for "context menu" items.
        See :class:`listing.Context<codequick.listing.Context>` for more details.
        """

        self.params = Params()
        """
        Dictionary like object for parameters that will be passed to the "callback" function.

        :example:
            >>> item = Listitem()
            >>> item.params['videoid'] = 'kqmdIV_gBfo'
        """

        self.property = Property(listitem)
        """
        Dictionary like object that allows you to add "listitem properties". e.g. "StartOffset".

        Some of these are processed internally by Kodi, such as the "StartOffset" property,
        which is the offset in seconds at which to start playback of an item. Others may be used
        in the skin to add extra information, such as "WatchedCount" for tvshow items.

        :examples:
            >>> item = Listitem()
            >>> item.property['StartOffset'] = '256.4'
        """

    @property
    def label(self):  # type: () -> str
        """
        The listitem label property.

        :example:
            >>> item = Listitem()
            >>> item.label = "Video Title"
        """
        label = self.listitem.getLabel()
        return label.decode("utf8") if isinstance(label, bytes) else label

    @label.setter
    def label(self, label):  # type: (str) -> None
        self.listitem.setLabel(label)
        unformatted_label = strip_formatting("", label)
        self.params["_title_"] = unformatted_label
        self.info["title"] = unformatted_label

    def set_callback(self, callback, *args, **kwargs):
        """
        Set the "callback" object.

        The "callback" parameter can be any of the following:
            * :class:`codequick.Script<codequick.script.Script>` callback.
            * :class:`codequick.Route<codequick.route.Route>` callback.
            * :class:`codequick.Resolver<codequick.resolver.Resolver>` callback.
            * The path to a callback function. i.e. "/main/menu/"
            * Any kodi path, e.g. "plugin://" or "script://"
            * Directly playable URL.

        .. note::

            By default kodi plugin / script paths are treated as playable items.
            To override this behavior, you can pass in the ``is_playable`` and ``is_folder`` parameters.
            If only ``is_folder`` is given, then ``is_playable`` will default to ``not is_folder``.

        :param callback: The "callback" or playable URL.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        """
        self.is_folder = is_folder = kwargs.pop("is_folder", self.is_folder)
        self.is_playable = kwargs.pop("is_playable", not is_folder)
        if callback in dispatcher.registered_routes:
            callback = dispatcher.registered_routes[callback].callback

        self.path = callback
        self._args = args
        if kwargs:
            self.params.update(kwargs)

    # noinspection PyProtectedMember
    def _close(self):
        path = self.path
        listitem = self.listitem
        if hasattr(path, "route"):
            isfolder = path.route.is_folder
            listitem.setProperty("isplayable", str(path.route.is_playable).lower())
            listitem.setProperty("folder", str(path.route.is_folder).lower())
            path = build_path(path, self._args, self.params.raw_dict)
        elif not path:
            listitem.setProperty("isplayable", "false")
            listitem.setProperty("folder", "false")
            isfolder = False
        else:
            listitem.setProperty("isplayable", str(self.is_playable).lower())
            listitem.setProperty("folder", str(self.is_folder).lower())
            isfolder = self.is_folder

        if not isfolder:
            # Add mediatype if not already set
            if "mediatype" not in self.info.raw_dict and self._content_type in ("video", "music"):  # pragma: no branch
                self.info.raw_dict["mediatype"] = self._content_type

            # Set the listitem subtitles
            if self.subtitles:
                self.listitem.setSubtitles(self.subtitles)

            # Add Video Specific Context menu items
            self.context.append(("$LOCALIZE[13347]", "XBMC.Action(Queue)"))
            self.context.append(("$LOCALIZE[13350]", "XBMC.ActivateWindow(videoplaylist)"))

            # Close video related datasets
            self.stream._close()

        # Set label to UNKNOWN if unset
        if not self.label:  # pragma: no branch
            self.label = u"UNKNOWN"

        # Close common datasets
        listitem.setPath(path)
        self.property._close()
        self.context._close()
        self.info._close(self._content_type)
        self.art._close(isfolder)

        # Return a tuple compatible with 'xbmcplugin.addDirectoryItems'
        return path, listitem, isfolder

    @classmethod
    def from_dict(
            cls,
            callback,
            label,
            art=None,
            info=None,
            stream=None,
            context=None,
            properties=None,
            params=None,
            subtitles=None
    ):
        """
        Constructor to create a "listitem".

        This method will create and populate a listitem from a set of given values.

        :type label: str
        :param callback: The "callback" function or playable URL.
        :param label: The listitem's label.
        :param dict art: Dictionary of listitem art.
        :param dict info: Dictionary of infoLabels.
        :param dict stream: Dictionary of stream details.
        :param list context: List of "context menu" item(s) containing "tuples" of ("label", "command") pairs.
        :param dict properties: Dictionary of listitem properties.
        :param dict params: Dictionary of parameters that will be passed to the "callback" function.
        :param list subtitles: List of paths to subtitle files.

        :return: A listitem object.
        :rtype: Listitem

        :example:
            >>> params = {"url": "http://example.com"}
            >>> item = {"label": "Video Title", "art": {"thumb": "http://example.com/image.jpg"}, "params": params}
            >>> listitem = Listitem.from_dict(**item)
        """
        item = cls()
        item.set_callback(callback)
        item.label = label

        if params:  # pragma: no branch
            item.params.update(params)
        if info:  # pragma: no branch
            item.info.update(info)
        if art:  # pragma: no branch
            item.art.update(art)
        if stream:  # pragma: no branch
            item.stream.update(stream)
        if properties:  # pragma: no branch
            item.property.update(properties)
        if context:  # pragma: no branch
            item.context.extend(context)
        if subtitles:  # pragma: no branch
            item.subtitles.extend(subtitles)

        return item

    @classmethod
    def next_page(cls, *args, **kwargs):
        """
        Constructor for adding link to "Next Page" of content.

        The current running "callback" will be called with all of the parameters that are given here.
        You can also specify which "callback" will be called by setting a keywork only argument called 'callback'.

        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.

        :example:
            >>> item = Listitem()
            >>> item.next_page(url="http://example.com/videos?page2")
        """
        # Current running callback
        callback = dispatcher.get_route().callback
        callback = kwargs.pop("callback", callback)

        # Add support params to callback params
        kwargs["_updatelisting_"] = True if u"_nextpagecount_" in dispatcher.params else False
        kwargs["_title_"] = dispatcher.params.get(u"_title_", u"")
        kwargs["_nextpagecount_"] = dispatcher.params.get(u"_nextpagecount_", 1) + 1

        # Create listitem instance
        item = cls()
        label = u"%s %i" % (Script.localize(NEXT_PAGE), kwargs["_nextpagecount_"])
        item.info["plot"] = Script.localize(NEXT_PAGE_PLOT)
        item.label = bold(label)
        item.art.global_thumb("next.png")
        item.set_callback(callback, *args, **kwargs)
        return item

    @classmethod
    def recent(cls, callback, *args, **kwargs):
        """
        Constructor for adding "Recent Videos" folder.

        This is a convenience method that creates the listitem with "name", "thumbnail" and "plot", already preset.

        :param callback: The "callback" function.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        """
        # Create listitem instance
        item = cls()
        item.label = bold(Script.localize(RECENT_VIDEOS))
        item.info["plot"] = Script.localize(RECENT_VIDEOS_PLOT)
        item.art.global_thumb("recent.png")
        item.set_callback(callback, *args, **kwargs)
        return item

    @classmethod
    def search(cls, callback, *args, **kwargs):
        """
        Constructor to add "saved search" support to add-on.

        This will first link to a "sub" folder that lists all saved "search terms". From here,
        "search terms" can be created or removed. When a selection is made, the "callback" function
        that was given will be executed with all parameters forwarded on. Except with one extra
        parameter, ``search_query``, which is the "search term" that was selected.

        :param callback: Function that will be called when the "listitem" is activated.
        :param args: "Positional" arguments that will be passed to the callback.
        :param kwargs: "Keyword" arguments that will be passed to the callback.
        :raises ValueError: If the given "callback" function does not have a ``search_query`` parameter.
        """
        from resources.lib.codequick.search import SavedSearches

        # Check that callback function has required parameter(search_query)
        if "search_query" not in callback.route.arg_names():
            raise ValueError("callback function is missing required argument: 'search_query'")

        if args:
            # Convert positional arguments to keyword arguments
            callback.route.args_to_kwargs(args, kwargs)

        item = cls()
        item.label = bold(Script.localize(SEARCH))
        item.art.global_thumb("search.png")
        item.info["plot"] = Script.localize(SEARCH_PLOT)
        item.set_callback(SavedSearches, _route=callback.route.path, first_load=True, **kwargs)
        return item

    @classmethod
    def youtube(cls, content_id, label=None, enable_playlists=True):
        """
        Constructor to add a "YouTube channel" to add-on.

        This listitem will list all videos from a "YouTube", channel or playlist. All videos will have a
        "Related Videos" option via the context menu. If ``content_id`` is a channel ID and ``enable_playlists``
        is ``True``, then a link to the "channel playlists" will also be added to the list of videos.

        :param str content_id: Channel ID or playlist ID, of video content.
        :param str label: [opt] Listitem Label. (default => "All Videos").
        :param bool enable_playlists: [opt] Set to ``False`` to disable linking to channel playlists.
                                      (default => ``True``)

        :example:
            >>> item = Listitem()
            >>> item.youtube("UC4QZ_LsYcvcq7qOsOhpAX4A")
        """
        from resources.lib.codequick.youtube import Playlist

        # Youtube exists, Creating listitem link
        item = cls()
        item.label = label if label else bold(Script.localize(ALLVIDEOS))
        item.art.global_thumb("videos.png")
        item.params["contentid"] = content_id
        item.params["enable_playlists"] = False if content_id.startswith("PL") else enable_playlists
        item.set_callback(Playlist)
        return item

    def __repr__(self):
        """Returns representation of the object."""
        return "{}('{}')".format(self.__class__.__name__, ensure_native_str(self.label))
