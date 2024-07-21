# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from functools import reduce
from random import getrandbits
from typing import Optional, Dict, Any, List, Union

import xbmcgui

from resources.lib.addonsettings import AddonSettings
from resources.lib import kodifactory
from resources.lib.logger import Logger
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib import mediatype
from resources.lib import contenttype
from resources.lib.retroconfig import Config
from resources.lib.streams.adaptive import Adaptive
from resources.lib.proxyinfo import ProxyInfo


# Don't make this an MediaItem(object) as it breaks the pickles
class MediaItem:
    """Main class that represent items that are retrieved in Retrospect. They are used
    to fill the lists and have MediaStreams in this hierarchy:

    MediaItem
        +- MediaStream
        +- MediaStream
        +- MediaStream

    """

    actionUrl: Optional[str]
    cacheToDisc: bool
    complete: bool
    content_type: str
    description: str
    dontGroup: bool
    episode: int
    fanart: str
    HttpHeaders: Dict[str, str]
    icon: str
    isCloaked: bool
    isDrmProtected: bool
    isGeoLocked: bool
    isLive: bool
    isPaid: bool
    items: List["MediaItem"]
    media_type: Optional[str]
    metaData: Dict[Any, Any]
    name: str
    postData: Optional[str]
    poster: str
    postJson: Optional[dict]
    streams: List["MediaStream"]
    subtitle: Optional[str]
    thumb: str
    tv_show_title: Optional[str]
    url: str

    LabelEpisode = "Episode"
    LabelTrackNumber = "TrackNumber"
    LabelDuration = "Duration"
    LabelTvShowTitle = "TVShowTitle"
    ExpiresAt = LanguageHelper.get_localized_string(LanguageHelper.ExpiresAt)

    #noinspection PyShadowingBuiltins
    def __init__(self, title, url, media_type=mediatype.FOLDER, depickle=False, tv_show_title=None):
        """ Creates a new MediaItem.

        The `url` can contain an url to a site more info about the item can be
        retrieved, for instance for a video item to retrieve the media url, or
        in case of a folder where child items can be retrieved.

        Essential is that no encoding (like UTF8) is specified in the title of
        the item. This is all taken care of when creating Kodi items in the
        different methods.

        :param str title:               The title of the item, used for appearance in lists.
        :param str url:                 Url that used for further information retrieval.
        :param str|None media_type:     The Kodi media type: video, movie, tvshow, season, episode,
                                        or musicvideo.
        :param bool depickle:           Is the constructor called while depickling.
        :param str|None tv_show_title:  The title of the TV Show to which the episode belongs.

        """

        name = title.strip()

        self.name = name
        self.tv_show_title = tv_show_title
        self.url = url
        self.actionUrl = None
        self.postData = None
        self.postJson = None

        self.description = ""
        self.thumb = ""                           # : The thumbnail (16:9, min 520x293)
        self.fanart = ""                          # : The fanart url (16:9, min 720p)
        self.icon = ""                            # : Low quality icon for list (1:1, min 256x256)
        self.poster = ""                          # : Poster artwork (2:3, min 500x750)

        self.__date = ""                          # : value show in interface
        self.__timestamp = datetime.min           # : value for sorting, this one is set to minimum so if non is set, it's shown at the bottom
        self.__expires_datetime = None            # : datetime value of the expire time

        self.dontGroup = False                    # : if set to True this item will not be auto grouped.
        self.isLive = False                       # : if set to True, the item will have a random QuerySting param
        self.cacheToDisc = True                   # : cache the content to disk so Kodi will not refetch
        self.isGeoLocked = False                  # : if set to True, the item is GeoLocked to the channels language (o)
        self.isDrmProtected = False               # : if set to True, the item is DRM protected and cannot be played (^)
        self.isPaid = False                       # : if set to True, the item is a Paid item and cannot be played (*)
        self.season = 0                           # : The season number
        self.episode = 0                          # : The episode number
        self.__infoLabels = dict()                # : Additional Kodi InfoLabels

        self.complete = False
        self.items = []
        self.HttpHeaders = dict()                 # : http headers for the item data retrieval

        # Items that are not essential for pickled
        self.isCloaked = False
        self.metaData = dict()                    # : Additional data that is for internal / routing use only

        # Kodi media types: video, movie, tvshow, season, episode or musicvideo, music, song, album, artist
        self.media_type = media_type
        # Kodi content types: files, songs, artists, albums, movies, tvshows, episodes,
        # musicvideos, videos, images, games. Defaults to 'episodes'
        self.content_type = contenttype.EPISODES

        self.streams = []
        self.subtitle = None

        if depickle:
            # While deplickling we don't need to do the guid/guidValue calculations. They will
            # be set from the __setstate__()
            return

        # GUID used for identification of the object. Do not set from script, MD5 needed
        # to prevent UTF8 issues
        self.__guid = None
        self.__guid_value = None

    @property
    def guid(self):
        """ Returns the item's GUID

        :rtype: str

        """

        if not self.__guid:
            self.__set_guids()

        return self.__guid

    @property
    def guid_value(self):
        """ Returns the guid's int value that can be used for hashing. """
        if not self.__guid_value:
            self.__set_guids()

        return self.__guid_value

    def add_stream(self, url, bitrate=0, subtitle=None):
        """ Appends a single stream to  this MediaItem.

        This methods adds a new MediaStream the MediaItem's streams collection.

        :param str url:         Url of the stream.
        :param int bitrate:     Bitrate of the stream (default = 0).
        :param str subtitle:    Url of the subtitle of the this Mediaitem..

        :return: A reference to the created MediaStream.
        :rtype: MediaStream

        """

        stream = MediaStream(url, bitrate)
        self.streams.append(stream)

        if subtitle:
            self.subtitle = subtitle

        return stream

    def has_streams(self):
        """ Return True if there are any MediaStreams present for this MediaItem

        :return: True if there are any MediaStreams present this MediaItem
        :rtype: bool

        """

        return len(self.streams) > 0

    @property
    def is_playable(self):
        """ Returns True if the item can be played in a Media Player.

        :return: Returns true if this is a playable MediaItem
        :rtype: bool

        """

        return self.media_type in mediatype.PLAYABLE_TYPES

    @property
    def is_folder(self):
        """ Indication if this item represents a folder.

        :return: True if this item is a folder item. False otherwise.
        :rtype: bool

        """
        return self.media_type in mediatype.FOLDER_TYPES

    @property
    def is_video(self):
        """ Indication if this item represents a video.

        :return: True if this item is a video item. False otherwise.
        :rtype: bool

        """
        return self.media_type in mediatype.VIDEO_TYPES

    @property
    def is_audio(self):
        """ Indication if this item represents a audio item.

        :return: True if this item is a audio item. False otherwise.
        :rtype: bool

        """
        return self.media_type in mediatype.AUDIO_TYPES

    @property
    def is_search_folder(self) -> bool:
        return self.is_folder and "retrospect:needle" in self.metaData

    def has_track(self):
        """ Does this MediaItem have a TrackNumber InfoLabel

        :return: if the track was set.
        :rtype: bool
        """

        return MediaItem.LabelTrackNumber in self.__infoLabels

    def has_date(self):
        """ Returns if a date was set

        :return: True if a date was set.
        :rtype: bool

        """

        return self.__timestamp > datetime.min

    def clear_date(self):
        """ Resets the date (used for favourites for example). """

        self.__timestamp = datetime.min
        self.__date = ""

    def has_info(self):
        """ Indicator to show that this item has additional InfoLabels

        :return: whether or not there are infolabels
        :rtype: bool

        """
        return bool(self.__infoLabels)

    def get_info_label(self, label):
        """ Retrieves an info label.

        :param str label:   The label name to retrieve.

        :return: The value of the label or None if it was not present
        :rtype: str|int|bool

        """

        return self.__infoLabels.get(label)

    def set_info_label(self, label, value):
        """ Set a Kodi InfoLabel and its value.

        See https://kodi.wiki/view/InfoLabels
        :param str label: the name of the label
        :param Any value: the value to assign

        """

        self.__infoLabels[label] = value

    def has_info_label(self, label):
        """ Indication of a specific info label is present

        :param str label:   The info label to check.

        :returns: In boolean whether the info label exists.
        :rtype: bool

        """

        return label in self.__infoLabels

    def set_artwork(self, icon=None, thumb=None, fanart=None, poster=None):
        """ Set the artwork for this MediaItem.

        :param str icon:    Url/path to icon (1:1, minimal 256x256).
        :param str thumb:   Url/path to thumbnail (16:9, minimal 520x293).
        :param str fanart:  Url/Path to fanart (16:9, minimal 1280x720).
        :param str poster:  Url/Path to poster (2:3, minimal 500x750)

        """

        # TODO: in the future change this to self.__artwork = {} that matches the Kodi ABI call.
        self.icon = icon or self.icon
        self.thumb = thumb or self.thumb
        self.fanart = fanart or self.fanart
        self.poster = poster or self.poster

    def set_season_info(self, season, episode, tv_show_title=None):
        """ Set season and episode information

        :param str|int season:  The Season Number
        :param str|int episode: The Episode Number
        :param str|None: The name of the TV Show

        """

        if season is None or episode is None:
            Logger.warning("Cannot set EpisodeInfo without season and episode")
            return

        if season:
            self.season = int(season)
            self.__infoLabels["Season"] = self.season

        if episode:
            self.episode = int(episode)
            self.__infoLabels["Episode"] = self.episode

        if tv_show_title:
            self.tv_show_title = tv_show_title
        return

    def set_expire_datetime(self, timestamp, year=0, month=0, day=0, hour=0, minutes=0, seconds=0):
        """ Sets the datetime value until when the item can be streamed.

        :param datetime|None timestamp: A full datetime object.
        :param int|str year:            The year of the datetime.
        :param int|str month:           The month of the datetime.
        :param int|str day:             The day of the datetime.
        :param int|str|None hour:       The hour of the datetime (Optional)
        :param int|str|None minutes:    The minutes of the datetime (Optional)
        :param int|str|None seconds:    The seconds of the datetime (Optional)

        """

        if timestamp is not None:
            self.__expires_datetime = timestamp
            return

        self.__expires_datetime = datetime(
            int(year), int(month), int(day), int(hour), int(minutes), int(seconds))

    def get_upnext_sort_key(self):
        """ Returns a value that be used to sort episodes for UpNext integration.

        :return: A key used to sort the items chronologically.
        :rtype: str

        """

        return "{:03d}-{:03d}-{}-{}".format(
            self.season,
            self.episode,
            self.__timestamp.strftime("%Y.%m.%d") if self.__timestamp.year > 1900 else "0001.01.01",
            self.name)

    def set_date(self, year, month, day,
                 hour=None, minutes=None, seconds=None, only_if_newer=False, text=None):
        """ Sets the datetime of the MediaItem.

        Sets the datetime of the MediaItem in the self.__date and the
        corresponding text representation of that datetime.

        `hour`, `minutes` and `seconds` can be optional and will be set to 0 in
        that case. They must all be set or none of them. Not just one or two of
        them.

        If `only_if_newer` is set to True, the update will only occur if the set
        datetime is newer then the currently set datetime.

        The text representation can be overwritten by setting the `text` keyword
        to a specific value. In that case the timestamp is set to the given time
        values but the text representation will be overwritten.

        If the values form an invalid datetime value, the datetime value will be
        reset to their default values.

        :param int|str year:            The year of the datetime.
        :param int|str month:           The month of the datetime.
        :param int|str day:             The day of the datetime.
        :param int|str|none hour:       The hour of the datetime (Optional)
        :param int|str|none minutes:    The minutes of the datetime (Optional)
        :param int|str|none seconds:     The seconds of the datetime (Optional)
        :param bool only_if_newer:      Update only if the new date is more recent then the
                                        currently set one
        :param str text:                If set it will overwrite the text in the date label the
                                        datetime is also set.

        :return: The datetime that was set.
        :rtype: datetime

        """

        # date_format = xbmc.getRegion('dateshort')
        # correct a small bug in Kodi
        # date_format = date_format[1:].replace("D-M-", "%D-%M")
        # dateFormatLong = xbmc.getRegion('datelong')
        # timeFormat = xbmc.getRegion('time')
        # date_time_format = "%s %s" % (date_format, timeFormat)

        try:
            date_format = "%Y-%m-%d"     # "%x"
            date_time_format = date_format + " %H:%M"

            if hour is None and minutes is None and seconds is None:
                time_stamp = datetime(int(year), int(month), int(day))
                date = time_stamp.strftime(date_format)
            else:
                time_stamp = datetime(int(year), int(month), int(day), int(hour), int(minutes), int(seconds))
                date = time_stamp.strftime(date_time_format)

            if only_if_newer and self.__timestamp > time_stamp:
                return

            self.__timestamp = time_stamp
            if text is None:
                self.__date = date
            else:
                self.__date = text

        except ValueError:
            Logger.error("Error setting date: Year=%s, Month=%s, Day=%s, Hour=%s, Minutes=%s, Seconds=%s", year, month, day, hour, minutes, seconds, exc_info=True)
            self.__timestamp = datetime.min
            self.__date = ""

        return self.__timestamp

    def get_date(self):
        """ Gets the object's date.

        :returns: the date for the object
        :rtype: str|None
        """
        return self.__date

    def get_kodi_item(self, name=None):
        """Creates a Kodi item with the same data is the MediaItem.

        This item is used for displaying purposes only and changes to it will
        not be passed on to the MediaItem.

        :param str|unicode name:    Overwrites the name of the Kodi item.

        :return: a complete Kodi ListItem
        :rtype: xbmcgui.ListItem

        """

        # Update name and descriptions
        name_post_fix, description_pre_fix = self.__update_title_and_description_with_limitations()

        name = self.__get_title(name)
        name = "%s %s" % (name, name_post_fix)
        name = self.__full_decode_text(name)

        if self.description is None:
            self.description = ''

        if description_pre_fix != "":
            description = "%s\n\n%s" % (description_pre_fix, self.description)
        else:
            description = self.description

        description = self.__full_decode_text(description)
        if description is None:
            description = ""

        # the Kodi ListItem date
        # date: string (%d.%m.%Y / 01.01.2009) - file date
        if self.__timestamp > datetime.min:
            kodi_date = self.__timestamp.strftime("%d.%m.%Y")
            kodi_year = self.__timestamp.year
        else:
            kodi_date = ""
            kodi_year = 0

        # Get all the info labels starting with the ones set and then add the specific ones
        info_labels = self.__infoLabels.copy()
        info_labels["Title"] = name

        if self.media_type and self.media_type != mediatype.PAGE:
            info_labels["mediatype"] = self.media_type

        if kodi_date:
            info_labels["Date"] = kodi_date
            info_labels["Year"] = kodi_year
            info_labels["Aired"] = kodi_date
        if self.media_type in (mediatype.VIDEO_TYPES | mediatype.FOLDER_TYPES):
            info_labels["Plot"] = description
        if self.tv_show_title:
            info_labels[MediaItem.LabelTvShowTitle] = self.tv_show_title

        # now create the Kodi item
        item = kodifactory.list_item(name or "<unknown>", self.__date)
        item.setLabel(name)
        item.setLabel2(self.__date)

        # set a flag to indicate it is a item that can be used with setResolveUrl.
        if self.is_playable:
            Logger.trace("Setting IsPlayable to True")
            item.setProperty("IsPlayable", "true")

        # specific items
        Logger.trace("Setting InfoLabels: %s", info_labels)
        if self.media_type in mediatype.AUDIO_TYPES:
            item.setInfo(type="music", infoLabels=info_labels)
        else:
            item.setInfo(type="video", infoLabels=info_labels)

        # now set all the art to prevent duplicate calls to Kodi
        art = {'thumb': self.thumb, 'icon': self.icon, 'landscape': self.thumb}
        if self.fanart and not AddonSettings.hide_fanart():
            art['fanart'] = self.fanart
        if self.poster:
            art['poster'] = self.poster
        item.setArt(art)

        item.setContentLookup(False)
        return item

    def get_resolved_kodi_item(self, bitrate, proxy=None):
        """ Retrieves a resolved kodi ListItem.

        :param int bitrate:             The bitrate of the streams that should be in the
                                        playlist. Given in kbps.
        :param ProxyInfo|None proxy:    The proxy to set

        :return: A Kodi ListItem with a resolved path and that path.
        :rtype: tuple[xbmcgui.ListItem, str]

        """

        Logger.info("Creating a Kodi ListItem for Bitrate: %s kbps\n%s\nMediaType: %s",
                    bitrate, self, self.media_type)

        if bitrate is None:
            raise ValueError("Bitrate not specified")

        if len(self.streams) == 0:
            Logger.warning("Ignoring empty MediaItem: %s", self)
            return None, None

        kodi_item = self.get_kodi_item()

        stream = self.__get_matching_stream(bitrate=bitrate)
        if stream.Adaptive and bitrate > 0:
            Adaptive.set_max_bitrate(stream, max_bit_rate=bitrate)

        # Set the actual stream path
        kodi_item.setPath(path=stream.Url)

        # properties of the Part
        for prop in stream.Properties:
            Logger.trace("Adding property: %s", prop)
            kodi_item.setProperty(prop[0], prop[1])

        # TODO: Apparently if we use the InputStream Adaptive, using the setSubtitles() causes sync issues.
        if self.subtitle and False:
            Logger.debug("Adding subtitle to ListItem: %s", self.subtitle)
            kodi_item.setSubtitles([self.subtitle, ])

        # Set any custom Header
        header_params = dict()

        # set proxy information if present
        self.__set_kodi_proxy_info(kodi_item, stream, stream.Url, header_params, proxy)

        # Now add the actual HTTP headers
        for k in stream.HttpHeaders:
            header_params[k] = HtmlEntityHelper.url_encode(stream.HttpHeaders[k])

        stream_url = stream.Url
        if header_params:
            kodi_query_string = reduce(
                lambda x, y: "%s&%s=%s" % (x, y, header_params[y]), header_params.keys(), "")
            kodi_query_string = kodi_query_string.lstrip("&")
            Logger.debug("Adding Kodi Stream parameters: %s\n%s", header_params, kodi_query_string)
            stream_url = "%s|%s" % (stream.Url, kodi_query_string)

        Logger.info("Playing Stream: %s", stream)
        return kodi_item, stream_url

    @property
    def uses_external_addon(self):
        return (self.url is not None
                and self.url.startswith("plugin://")
                and not self.url.startswith(f"plugin://{Config.addonId}"))

    @property
    def title(self):
        return self.name

    def __get_matching_stream(self, bitrate):
        """ Returns the MediaStream for the requested bitrate.

        Arguments:
        bitrate : integer - The bitrate of the stream in kbps

        Returns:
        The url of the stream with the requested bitrate.

        If bitrate is not specified the highest bitrate stream will be used.

        """

        # order the items by bitrate
        self.streams.sort(key=lambda s: s.Bitrate)
        best_stream = None
        best_distance = None

        if bitrate == 0:
            # return the highest one
            Logger.debug("Returning the higest bitrate stream")
            return self.streams[-1]

        for stream in self.streams:
            if stream.Bitrate is None:
                # no bitrate set, see if others are available
                continue

            # this is the bitrate-as-max-limit-method
            if stream.Bitrate > bitrate:
                # if the bitrate is higher, continue for more
                continue
            # if commented ^^ , we get the closest-match-method

            # determine the distance till the bitrate
            distance = abs(bitrate - stream.Bitrate)

            if best_distance is None or best_distance > distance:
                # this stream is better, so store it.
                best_distance = distance
                best_stream = stream

        if best_stream is None:
            # no match, take the lowest bitrate
            return self.streams[0]

        return best_stream

    def __set_kodi_proxy_info(self, kodi_item, stream, stream_url, kodi_params, proxy):
        """ Updates a Kodi ListItem with the correct Proxy configuration taken from the ProxyInfo
        object.

        :param xbmcgui.ListItem kodi_item:          The current Kodi ListItem.
        :param MediaStream stream:                  The current Stream object.
        :param str stream_url:                      The current Url for the Stream object (might have
                                                    been changed in the mean time by other calls)
        :param dict[str|unicode,str] kodi_params:   A dictionary of Kodi Parameters.
        :param ProxyInfo proxy:                     The ProxyInfo object

        """
        if not proxy:
            return

        if proxy.Scheme.startswith("http") and not stream.Url.startswith("http"):
            Logger.debug("Not adding proxy due to scheme mismatch")
        elif proxy.Scheme == "dns":
            Logger.debug("Not adding DNS proxy for Kodi streams")
        elif not proxy.use_proxy_for_url(stream_url):
            Logger.debug("Not adding proxy due to filter mismatch")
        else:
            if AddonSettings.is_min_version(AddonSettings.KodiKrypton):
                # See ffmpeg proxy in https://github.com/xbmc/xbmc/commit/60b21973060488febfdc562a415e11cb23eb9764
                kodi_item.setProperty("proxy.host", proxy.Proxy)
                kodi_item.setProperty("proxy.port", str(proxy.Port))
                kodi_item.setProperty("proxy.type", proxy.Scheme)
                if proxy.Username:
                    kodi_item.setProperty("proxy.user", proxy.Username)
                if proxy.Password:
                    kodi_item.setProperty("proxy.password", proxy.Password)
                Logger.debug("Adding (Krypton) %s", proxy)
            else:
                kodi_params["HttpProxy"] = proxy.get_proxy_address()
                Logger.debug("Adding (Pre-Krypton) %s", proxy)
        return

    def __set_guids(self):
        """ Generates a Unique Identifier based on Time and Random Integers """

        try:
            self.__guid = "%s%s" % (
                EncodingHelper.encode_md5(self.name), EncodingHelper.encode_md5(self.url or ""))
            self.__guid_value = int("0x%s" % (self.guid,), 0)

            # For live items and search, append a random part to the textual guid, as these items
            # actually have different content for the same URL.
            if self.isLive:
                self.__guid = "%s%s" % (self.__guid, ("%0x" % getrandbits(8 * 4)).upper())
        except:
            Logger.error("Error setting GUID for title:'%s' and url:'%s'. Falling back to UUID",
                         self.title, self.url, exc_info=True)
            # Slower code
            # self.__guid = binascii.hexlify(os.urandom(16)).decode().upper()
            self.__guid = "%0x" % getrandbits(32 * 4)
            self.__guid_value = int("0x%s" % (self.guid,), 0)

    def __full_decode_text(self, string_value):
        """ Decodes a byte encoded string with HTML content into Unicode String

        Arguments:
        stringValue : string - The byte encoded string to decode

        Returns:
        An Unicode String with all HTML entities replaced by their UTF8 characters

        The decoding is done by first decode the string to UTF8 and then replace
        the HTML entities to their UTF8 characters.

        """

        if string_value is None:
            return None

        if string_value == "":
            return ""

        # then get rid of the HTML entities
        string_value = HtmlEntityHelper.convert_html_entities(string_value)
        return string_value

    def __str__(self):
        """ String representation 

        :return: The String representation
        :rtype: str

        """

        value = self.name

        if self.is_playable:
            if len(self.streams) > 0:
                value = "MediaItem: %s [Type=%s, Complete=%s, IsLive=%s, Date=%s, Geo/DRM=%s/%s]" % \
                        (value, self.media_type, self.complete, self.isLive, self.__date,
                         self.isGeoLocked, self.isDrmProtected)
                for media_stream in self.streams:
                    value = "%s\n%s" % (value, media_stream)
                value = "%s" % (value,)
            else:
                value = "%s [Type=%s, Complete=%s, unknown urls, IsLive=%s, Date=%s, Geo/DRM=%s/%s]" \
                        % (value, self.media_type, self.complete, self.isLive, self.__date,
                           self.isGeoLocked, self.isDrmProtected)
        else:
            value = "%s [Type=%s, Url=%s, Date=%s, IsLive=%s, Geo/DRM=%s/%s]" \
                    % (value, self.media_type, self.url, self.__date, self.isLive, self.isGeoLocked, self.isDrmProtected)

        if self.subtitle:
            value = "%s\n + Subtitle: %s" % (value, self.subtitle)

        return value

    def __eq__(self, item):
        """ checks 2 items for Equality

        Arguments:
        item : MediaItem - The item to check for equality.

        Returns:
        the output of self.__equals(item).

        """
        return self.__equals(item)

    def __ne__(self, item):
        """ returns NOT Equal

        Arguments:
        item : MediaItem - The item to check for equality.

        Returns:
        the output of not self.__equals(item).

        """

        return not self.__equals(item)

    def __hash__(self):
        """ returns the hash value """

        return hash(self.guid_value)

    def __equals(self, other):
        """ Checks two MediaItems for equality

        :param MediaItem other: The other item.

        :return: whether the objects are equal (if the item's GUID's match).
        :rtype: bool

        """

        if not other:
            return False

        return self.guid_value == other.guid_value

    def __update_title_and_description_with_limitations(self):
        """ Updates the title/name and description with the symbols for DRM, GEO and Paid.

        :return:            (tuple) name postfix, description postfix
        :rtype: tuple[str,str]

        """

        geo_lock = "&ordm;"  # º
        drm_lock = "^"       # ^
        paid = "&ordf;"     # ª
        cloaked = "&uml;"   # ¨
        description_prefix = []
        title_postfix = []

        description = ""
        title = ""

        if self.__expires_datetime is not None:
            expires = "{}: {}".format(MediaItem.ExpiresAt, self.__expires_datetime.strftime("%Y-%m-%d %H:%M"))
            description_prefix.append(("gold", expires))

        if self.isDrmProtected:
            title_postfix.append(("gold", drm_lock))
            description_prefix.append(
                ("gold", LanguageHelper.get_localized_string(LanguageHelper.DrmProtected))
            )

        if self.isGeoLocked:
            title_postfix.append(("aqua", geo_lock))
            description_prefix.append(
                ("aqua", LanguageHelper.get_localized_string(LanguageHelper.GeoLockedId))
            )

        if self.isPaid:
            title_postfix.append(("gold", paid))
            description_prefix.append(
                ("gold", LanguageHelper.get_localized_string(LanguageHelper.PremiumPaid))
            )

        if self.isCloaked:
            title_postfix.append(("gold", cloaked))
            description_prefix.append(
                ("gold", LanguageHelper.get_localized_string(LanguageHelper.HiddenItem))
            )

        if self.uses_external_addon:
            from resources.lib.xbmcwrapper import XbmcWrapper
            external = XbmcWrapper.get_external_add_on_label(self.url)
            title_postfix.append(("gold", external))

        def __color_text(texts, text_format="[COLOR {}]{}[/COLOR]"):
            """

            :param list[tuple[str, str]] texts:     The color and text (in tuple)
            :param str text_format:                 The format used for filling

            :return: A Kodi compatible color coded string.
            :rtype: str

            See https://forum.kodi.tv/showthread.php?tid=210837
            """

            return "".join([text_format.format(clr, text.lstrip()) for clr, text in texts]).strip()

        # actually update it
        if description_prefix:
            description = __color_text(description_prefix, text_format="[COLOR {}]{}[/COLOR]\n")

        if title_postfix:
            title = __color_text(title_postfix)

        return title, description

    def __get_title(self, name):
        """ Create the title based on the MediaItems name and type.

        :param str name: the name to update.

        :return: an updated name
        :rtype: str

        """

        if not name:
            name = self.name

        if self.media_type == mediatype.PAGE:
            # We need to add the Page prefix to the item
            name = "%s %s" % (LanguageHelper.get_localized_string(LanguageHelper.Page), name)
            Logger.debug("MediaItem.__get_title :: Adding Page Prefix")

        elif self.__date != '' and not self.is_playable \
                and not AddonSettings.is_min_version(AddonSettings.KodiLeia):
            # not playable items should always show date
            name = "%s [COLOR=dimgray](%s)[/COLOR]" % (name, self.__date)

        folder_prefix = AddonSettings.get_folder_prefix()
        if self.media_type in mediatype.FOLDER_TYPES and not folder_prefix == "":
            name = "%s %s" % (folder_prefix, name)

        return name

    def __setstate__(self, state):
        """ Sets the current MediaItem's state based on the pickled value. However, it also adds
        newly added class variables so old items won't brake. This happens with depickling.

        @param dict state: a default Pickle __dict__

        """

        # Convert older `MediaItem.type` to the new `mediatype` values.
        media_type = state.get("type")
        if media_type == "audio":
            media_type = mediatype.MUSIC
        elif media_type == "folder":
            media_type = mediatype.FOLDER
        elif media_type == "page":
            media_type = mediatype.PAGE
        elif media_type == "video":
            media_type = mediatype.VIDEO

        m = MediaItem(state["name"], state["url"], media_type=media_type, depickle=False)
        self.__dict__ = m.__dict__
        self.__dict__.update(state)

        # Any modification/fixes for older version could be done here
        return

    # Because this happens at pickle-time, it could still lead to issues if the __init__() would
    # change. The result for __reduce__() will be the same as with the __setstate_() solution.
    # def __reduce__(self):
    #     """ Define a __reduce__() method used to store the data to call __init__() when
    #     depickling items. This happens when pickling.
    #
    #     :return: a tuple with type, parameters and state
    #     :rtype: type, tuple, dict
    #
    #     """
    #
    #     return type(self), (self.name, self.url), self.__dict__


class FolderItem(MediaItem):
    def __init__(self, title, url, content_type, media_type=mediatype.FOLDER, depickle=False):
        """ Creates a new FolderItem.

        The `url` can contain an url to a site more info about the item can be
        retrieved, for instance for a video item to retrieve the media url, or
        in case of a folder where child items can be retrieved.

        Essential is that no encoding (like UTF8) is specified in the title of
        the item. This is all taken care of when creating Kodi items in the
        different methods.

        :param str title:               The title of the item, used for appearance in lists.
        :param str url:                 Url that used for further information retrieval.
        :param str|None media_type:     The Kodi media type: video, movie, tvshow, season, episode,
                                        or musicvideo.
        :param str|None content_type:   The Kodi content type of the child items: files, songs,
                                        artists, albums, movies, tvshows, episodes, musicvideos,
                                        videos, images, games. Defaults to 'episodes'
        :param bool depickle:           Is the constructor called while depickling.

        """

        MediaItem.__init__(self, title, url, media_type=media_type, depickle=depickle)
        self.content_type = content_type


# Don't make this an MediaItem(object) as it breaks the pickles
class MediaStream:
    """Class that represents a Mediastream with <url> and a specific <bitrate>"""

    def __init__(self, url, bitrate=0, *args):
        """Initialises a new MediaStream

        :param str url:                 The URL of the stream.
        :param int|str bitrate:         The bitrate of the stream (defaults to 0).
        :param tuple[str,str] args:     (name, value) for any stream property.

        """

        Logger.trace("Creating MediaStream '%s' with bitrate '%s'", url, bitrate)
        self.Url = url
        self.Bitrate = int(bitrate)
        self.Properties = []
        self.Adaptive = False
        self.HttpHeaders = dict()  # :  HTTP Headers for stream playback

        for prop in args:
            self.add_property(prop[0], prop[1])
        return

    def add_property(self, name, value):
        """ Appends a new property to the self.Properties dictionary. On playback
        these properties will be set to the Kodi PlaylistItem as properties.

        Example:    
        strm.add_property("inputstream", "inputstream.adaptive")
        strm.add_property("inputstream.adaptive.manifest_type", "mpd")

        :param str name:    The name of the property.
        :param str value:   The value of the property.

        """

        Logger.debug("Adding stream property: %s = %s", name, value)
        self.Properties.append((name, value))

    def __eq__(self, other):
        """ Checks 2 items for Equality

        Equality takes into consideration:

        * The url of the MediaStream

        :param MediaStream other:   The stream to check for equality.

        :return: True if the items are equal.
        :rtype: bool

        """

        # also check for URL
        if other is None:
            return False

        return self.Url == other.Url

    def __str__(self):
        """ String representation

        :return: The String representation
        :rtype: str

        """

        text = "MediaStream: %s [bitrate=%s]" % (self.Url, self.Bitrate)
        for prop in self.Properties:
            text = "%s\n    + Property: %s=%s" % (text, prop[0], prop[1])

        return text


MediaItemResult = Optional[Union[List[MediaItem], MediaItem]]
