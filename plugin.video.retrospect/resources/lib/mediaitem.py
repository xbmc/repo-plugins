# coding=utf-8  # NOSONAR
# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import os
from datetime import datetime
import binascii
from functools import reduce

import xbmcgui

from resources.lib.addonsettings import AddonSettings
from resources.lib.logger import Logger
from resources.lib.helpers.htmlentityhelper import HtmlEntityHelper
from resources.lib.helpers.encodinghelper import EncodingHelper
from resources.lib.helpers.languagehelper import LanguageHelper
from resources.lib.streams.adaptive import Adaptive
from resources.lib.proxyinfo import ProxyInfo


# Don't make this an MediaItem(object) as it breaks the pickles
class MediaItem:
    """Main class that represent items that are retrieved in XOT. They are used
    to fill the lists and have MediaItemParts which have MediaStreams in this
    hierarchy:

    MediaItem
        +- MediaItemPart
        |    +- MediaStream
        |    +- MediaStream
        |    +- MediaStream
        +- MediaItemPart
        |    +- MediaStream
        |    +- MediaStream
        |    +- MediaStream

    """

    LabelTrackNumber = "TrackNumber"
    LabelDuration = "Duration"
    ExpiresAt = LanguageHelper.get_localized_string(LanguageHelper.ExpiresAt)

    def __dir__(self):
        """ Required in order for the Pickler().Validate to work! """
        return ["name",
                "url",
                "actionUrl",
                "MediaItemParts",
                "description",
                "thumb",
                "fanart",
                "icon",
                "__date",
                "__timestamp",
                "type",
                "dontGroup",
                "isLive",
                "isGeoLocked",
                "isDrmProtected",
                "isPaid",
                "__infoLabels",
                "complete",
                "items",
                "HttpHeaders",
                "guid",
                "guidValue"]

    #noinspection PyShadowingBuiltins
    def __init__(self, title, url, type="folder"):
        """ Creates a new MediaItem.

        The `url` can contain an url to a site more info about the item can be
        retrieved, for instance for a video item to retrieve the media url, or
        in case of a folder where child items can be retrieved.

        Essential is that no encoding (like UTF8) is specified in the title of
        the item. This is all taken care of when creating Kodi items in the
        different methods.

        :param str|unicode title:   The title of the item, used for appearance in lists.
        :param str|unicode url:     Url that used for further information retrieval.
        :param str type:            Type of MediaItem (folder, video, audio). Defaults to 'folder'.

        """

        name = title.strip()

        self.name = name
        self.url = url
        self.actionUrl = None
        self.MediaItemParts = []
        self.description = ""
        self.thumb = ""                           # : The local or remote image for the thumbnail of episode
        self.fanart = ""                          # : The fanart url
        self.icon = ""                            # : low quality icon for list

        self.__date = ""                          # : value show in interface
        self.__timestamp = datetime.min           # : value for sorting, this one is set to minimum so if non is set, it's shown at the bottom
        self.__expires_datetime = None            # : datetime value of the expire time

        self.type = type                          # : video, audio, folder, append, page, playlist
        self.dontGroup = False                    # : if set to True this item will not be auto grouped.
        self.isLive = False                       # : if set to True, the item will have a random QuerySting param
        self.isGeoLocked = False                  # : if set to True, the item is GeoLocked to the channels language (o)
        self.isDrmProtected = False               # : if set to True, the item is DRM protected and cannot be played (^)
        self.isPaid = False                       # : if set to True, the item is a Paid item and cannot be played (*)
        self.__infoLabels = dict()                # : Additional Kodi InfoLabels

        self.complete = False
        self.items = []
        self.HttpHeaders = dict()                 # : http headers for the item data retrieval

        # Items that are not essential for pickled
        self.isCloaked = False
        self.metaData = dict()                    # : Additional data that is for internal / routing use only

        # GUID used for identification of the object. Do not set from script, MD5 needed
        # to prevent UTF8 issues
        try:
            self.guid = "%s%s" % (EncodingHelper.encode_md5(title), EncodingHelper.encode_md5(url or ""))
        except:
            Logger.error("Error setting GUID for title:'%s' and url:'%s'. Falling back to UUID", title, url, exc_info=True)
            self.guid = self.__get_uuid()
        self.guidValue = int("0x%s" % (self.guid,), 0)

    def append_single_stream(self, url, bitrate=0, subtitle=None):
        """ Appends a single stream to a new MediaPart of this MediaItem.

        This methods creates a new MediaPart item and adds the provided
        stream to its MediaStreams collection. The newly created MediaPart
        is then added to the MediaItem's MediaParts collection.

        :param str url:         Url of the stream.
        :param int bitrate:     Bitrate of the stream (default = 0).
        :param str subtitle:    Url of the subtitle of the mediapart.

        :return: A reference to the created MediaPart.
        :rtype: MediaItemPart

        """

        new_part = MediaItemPart(self.name, url, bitrate, subtitle)
        self.MediaItemParts.append(new_part)
        return new_part

    def create_new_empty_media_part(self):
        """ Adds an empty MediaPart to the MediaItem.

        This method is used to create an empty MediaPart that can be used to
        add new stream to. The newly created MediaPart is appended to the
        MediaItem.MediaParts list.

        :return: The new MediaPart object (as a reference) that was appended.
        :rtype: MediaItemPart

        """

        new_part = MediaItemPart(self.name)
        self.MediaItemParts.append(new_part)
        return new_part

    def has_media_item_parts(self):
        """ Return True if there are any MediaItemParts present with streams for
        this MediaItem

        :return: True if there are any MediaItemParts present with streams for
                 this MediaItem
        :rtype: bool

        """

        for part in self.MediaItemParts:
            if len(part.MediaStreams) > 0:
                return True

        return False

    def is_playable(self):
        """ Returns True if the item can be played in a Media Player.

        At this moment it returns True for:
        * type = 'video'
        * type = 'audio'

        :return: Returns true if this is a playable MediaItem
        :rtype: bool

        """

        return self.type.lower() in ('video', 'audio', 'playlist')

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

    def set_info_label(self, label, value):
        """ Set a Kodi InfoLabel and its value.

        See http://kodi.wiki/view/InfoLabels
        :param str label: the name of the label
        :param Any value: the value to assign

        """

        self.__infoLabels[label] = value

    def set_season_info(self, season, episode):
        """ Set season and episode information

        :param str|int season:  The Season Number
        :param str|int episode: The Episode Number

        """

        if season is None or episode is None:
            Logger.warning("Cannot set EpisodeInfo without season and episode")
            return

        self.__infoLabels["Episode"] = int(episode)
        self.__infoLabels["Season"] = int(season)
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
        if kodi_date:
            info_labels["Date"] = kodi_date
            info_labels["Year"] = kodi_year
            info_labels["Aired"] = kodi_date
        if self.type != "audio":
            info_labels["Plot"] = description

        # now create the Kodi item
        item = xbmcgui.ListItem(name or "<unknown>", self.__date)
        item.setLabel(name)
        item.setLabel2(self.__date)

        # set a flag to indicate it is a item that can be used with setResolveUrl.
        if self.is_playable():
            Logger.trace("Setting IsPlayable to True")
            item.setProperty("IsPlayable", "true")

        # specific items
        Logger.trace("Setting InfoLabels: %s", info_labels)
        if self.type == "audio":
            item.setInfo(type="music", infoLabels=info_labels)
        else:
            item.setInfo(type="video", infoLabels=info_labels)

        # now set all the art to prevent duplicate calls to Kodi
        if self.fanart and not AddonSettings.hide_fanart():
            item.setArt({'thumb': self.thumb, 'icon': self.icon, 'fanart': self.fanart})
        else:
            item.setArt({'thumb': self.thumb, 'icon': self.icon})

        # Set Artwork
        # art = dict()
        # for l in ("thumb", "poster", "banner", "fanart", "clearart", "clearlogo", "landscape"):
        #     art[l] = self.thumb
        # item.setArt(art)

        # We never set the content resolving, Retrospect does this. And if we do, then the custom
        # headers are removed from the URL when opening the resolved URL.
        try:
            item.setContentLookup(False)
        except:
            # apparently not yet supported on this Kodi version3
            pass
        return item

    def get_kodi_play_list_data(self, bitrate, proxy=None):
        """ Returns the playlist items for this MediaItem

        :param int bitrate:             The bitrate of the streams that should be in the
                                        playlist. Given in kbps.
        :param ProxyInfo|None proxy:    The proxy to set

        :return: A list of ListItems that should be added to a playlist with their selected
                 stream url
        :rtype: list[tuple[xbmcgui.ListItem, str]]

        """

        Logger.info("Creating playlist items for Bitrate: %s kbps\n%s", bitrate, self)

        if not bool(bitrate):
            raise ValueError("Bitrate not specified")

        play_list_data = []
        for part in self.MediaItemParts:
            if len(part.MediaStreams) == 0:
                Logger.warning("Ignoring empty MediaPart: %s", part)
                continue

            kodi_item = self.get_kodi_item()
            stream = part.get_media_stream_for_bitrate(bitrate)
            Logger.info("Selected Stream:  %s", stream)
            if stream.Adaptive:
                Adaptive.set_max_bitrate(stream, max_bit_rate=bitrate)

            # Set the actual stream path
            kodi_item.setProperty("path", stream.Url)

            # properties of the Part
            for prop in part.Properties + stream.Properties:
                Logger.trace("Adding property: %s", prop)
                kodi_item.setProperty(prop[0], prop[1])

            # TODO: Apparently if we use the InputStream Adaptive, using the setSubtitles() causes sync issues.
            if part.Subtitle and False:
                Logger.debug("Adding subtitle to ListItem: %s", part.Subtitle)
                kodi_item.setSubtitles([part.Subtitle, ])

            # Set any custom Header
            header_params = dict()

            # set proxy information if present
            self.__set_kodi_proxy_info(kodi_item, stream, stream.Url, header_params, proxy)

            # Now add the actual HTTP headers
            for k in part.HttpHeaders:
                header_params[k] = HtmlEntityHelper.url_encode(part.HttpHeaders[k])

            stream_url = stream.Url
            if header_params:
                kodi_query_string = reduce(
                    lambda x, y: "%s&%s=%s" % (x, y, header_params[y]), header_params.keys(), "")
                kodi_query_string = kodi_query_string.lstrip("&")
                Logger.debug("Adding Kodi Stream parameters: %s\n%s", header_params, kodi_query_string)
                stream_url = "%s|%s" % (stream.Url, kodi_query_string)

            play_list_data.append((kodi_item, stream_url))

        return play_list_data

    @property
    def uses_external_addon(self):
        return self.url is not None and self.url.startswith("plugin://")

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
            if AddonSettings.is_min_version(17):
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

    def __get_uuid(self):
        """ Generates a Unique Identifier based on Time and Random Integers """

        return binascii.hexlify(os.urandom(16)).upper()

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

        if self.is_playable():
            if len(self.MediaItemParts) > 0:
                value = "MediaItem: %s [Type=%s, Complete=%s, IsLive=%s, Date=%s, Geo/DRM=%s/%s]" % \
                        (value, self.type, self.complete, self.isLive, self.__date,
                         self.isGeoLocked, self.isDrmProtected)
                for media_part in self.MediaItemParts:
                    value = "%s\n%s" % (value, media_part)
                value = "%s" % (value,)
            else:
                value = "%s [Type=%s, Complete=%s, unknown urls, IsLive=%s, Date=%s, Geo/DRM=%s/%s]" \
                        % (value, self.type, self.complete, self.isLive, self.__date,
                           self.isGeoLocked, self.isDrmProtected)
        else:
            value = "%s [Type=%s, Url=%s, Date=%s, IsLive=%s, Geo/DRM=%s/%s]" \
                    % (value, self.type, self.url, self.__date, self.isLive, self.isGeoLocked, self.isDrmProtected)

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

        return hash(self.guidValue)

    def __equals(self, other):
        """ Checks two MediaItems for equality

        :param MediaItem other: The other item.

        :return: whether the objects are equal (if the item's GUID's match).
        :rtype: bool

        """

        if not other:
            return False

        return self.guidValue == other.guidValue

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
            description_prefix.append(expires)

        if self.isDrmProtected:
            title_postfix.append(drm_lock)
            description_prefix.append(
                LanguageHelper.get_localized_string(LanguageHelper.DrmProtected))

        if self.isGeoLocked:
            title_postfix.append(geo_lock)
            description_prefix.append(
                LanguageHelper.get_localized_string(LanguageHelper.GeoLockedId))

        if self.isPaid:
            title_postfix.append(paid)
            description_prefix.append(
                LanguageHelper.get_localized_string(LanguageHelper.PremiumPaid))

        if self.isCloaked:
            title_postfix.append(cloaked)
            description_prefix.append(
                LanguageHelper.get_localized_string(LanguageHelper.HiddenItem))

        if self.uses_external_addon:
            from resources.lib.xbmcwrapper import XbmcWrapper
            external = XbmcWrapper.get_external_add_on_label(self.url)
            title_postfix.append(external)

        # actually update it
        if description_prefix:
            description_prefix = "\n".join(description_prefix)
            description = "[COLOR gold][I]%s[/I][/COLOR]" % (description_prefix.rstrip(), )

        if title_postfix:
            title = "".join(title_postfix)
            title = "[COLOR gold]%s[/COLOR]" % (title.lstrip(), )

        return title, description

    def __get_title(self, name):
        """ Create the title based on the MediaItems name and type.

        :param str name: the name to update.

        :return: an updated name
        :rtype: str

        """

        if not name:
            name = self.name

        if self.type == 'page':
            # We need to add the Page prefix to the item
            name = "%s %s" % (LanguageHelper.get_localized_string(LanguageHelper.Page), name)
            Logger.debug("MediaItem.__get_title :: Adding Page Prefix")

        elif self.__date != '' and not self.is_playable() and not AddonSettings.is_min_version(18):
            # not playable items should always show date
            name = "%s [COLOR=dimgray](%s)[/COLOR]" % (name, self.__date)

        folder_prefix = AddonSettings.get_folder_prefix()
        if self.type == "folder" and not folder_prefix == "":
            name = "%s %s" % (folder_prefix, name)

        return name

    def __setstate__(self, state):
        """ Sets the current MediaItem's state based on the pickled value. However, it also adds
        newly added class variables so old items won't brake.

        @param state: a default Pickle __dict__
        """

        # creating a new MediaItem here should not cause too much performance issues, as not very many
        # will be depickled.

        m = MediaItem("", "")
        self.__dict__ = m.__dict__
        self.__dict__.update(state)

    # We are not using the __getstate__ for now
    # def __getstate__(self):
    #     return self.__dict__


# Don't make this an MediaItem(object) as it breaks the pickles
class MediaItemPart:
    """Class that represents a MediaItemPart"""

    def __init__(self, name, url="", bitrate=0, subtitle=None, *args):
        """ Creates a MediaItemPart with <name> with at least one MediaStream
        instantiated with the values <url> and <bitrate>.
        The MediaPart could also have a <subtitle> or Properties in the <*args>

        If a subtitles was provided, the subtitle will be downloaded and stored
        in the XOT cache. When played, the subtitle is shown. Due to the Kodi
        limitation only one subtitle can be set on a playlist, this will be
        the subtitle of the first MediaPartItem

        :param str name:                    The name of the MediaItemPart.
        :param str url:                     The URL of the stream of the MediaItemPart.
        :param int bitrate:                 The bitrate of the stream of the MediaItemPart.
        :param str|None subtitle:           The url of the subtitle of this MediaItemPart
        :param tuple[str,str] args:         A list of arguments that will be set as properties
                                            when getting an Kodi Playlist Item

        """

        Logger.trace("Creating MediaItemPart '%s' for '%s'", name, url)
        self.Name = name
        self.MediaStreams = []
        self.Subtitle = ""
        self.HttpHeaders = dict()                   # :  HTTP Headers for stream playback

        # set a subtitle
        if subtitle is not None:
            self.Subtitle = subtitle

        if not url == "":
            # set the stream that was passed
            self.append_media_stream(url, bitrate)

        # set properties
        self.Properties = []
        for prop in args:
            self.add_property(prop[0], prop[1])
        return

    def append_media_stream(self, url, bitrate, *args):
        """Appends a mediastream item to the current MediaPart

        The bitrate could be set to None.

        :param url:                     The url of the MediaStream.
        :param int|str bitrate:         The bitrate of the MediaStream.
        :param tuple[str,str] args:     A list of arguments that will be set as properties
                                        when getting an Kodi Playlist Item

        :return: The newly added MediaStream by reference.
        :rtype: MediaStream

        """

        stream = MediaStream(url, bitrate, *args)
        self.MediaStreams.append(stream)
        return stream

    def add_property(self, name, value):
        """ Adds a property to the MediaPart.

        Appends a new property to the self.Properties dictionary. On playback
        these properties will be set to the Kodi PlaylistItem as properties.

        :param str name:    The name of the property.
        :param str value:   The value of the property.

        """

        Logger.debug("Adding property: %s = %s", name, value)
        self.Properties.append((name, value))

    def get_media_stream_for_bitrate(self, bitrate):
        """Returns the MediaStream for the requested bitrate.

        Arguments:
        bitrate : integer - The bitrate of the stream in kbps

        Returns:
        The url of the stream with the requested bitrate.

        If bitrate is not specified the highest bitrate stream will be used.

        """

        # order the items by bitrate
        self.MediaStreams.sort(key=lambda s: s.Bitrate)
        best_stream = None
        best_distance = None

        for stream in self.MediaStreams:
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
            return self.MediaStreams[0]

        return best_stream

    def __eq__(self, other):
        """ Checks 2 items for Equality. Equality takes into consideration:

        * Name
        * Subtitle
        * Length of the MediaStreams
        * Compares all the MediaStreams in the self.MediaStreams

         :param MediaItemPart other: The part the test for equality.

         :return: Returns true if the items are equal.
         :rtype: bool

        """

        if other is None:
            return False

        if not other.Name == self.Name:
            return False

        if not other.Subtitle == self.Subtitle:
            return False

        # now check the stream
        if not len(self.MediaStreams) == len(other.MediaStreams):
            return False

        for i in range(0, len(self.MediaStreams)):
            if not self.MediaStreams[i] == other.MediaStreams[i]:
                return False

        # if we reach this point they are equal.
        return True

    def __str__(self):
        """ String representation for the MediaPart

        :return: The String representation
        :rtype: str

        """

        text = "MediaPart: %s [HttpHeaders=%s]" % (self.Name, self.HttpHeaders)

        if self.Subtitle != "":
            text = "%s\n + Subtitle: %s" % (text, self.Subtitle)

        for prop in self.Properties:
            text = "%s\n + Property: %s=%s" % (text, prop[0], prop[1])

        for stream in self.MediaStreams:
            text = "%s\n + %s" % (text, stream)
        return text


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

        for prop in args:
            self.add_property(prop[0], prop[1])
        return

    def add_property(self, name, value):
        """ Appends a new property to the self.Properties dictionary. On playback
        these properties will be set to the Kodi PlaylistItem as properties.

        Example:    
        strm.add_property("inputstreamaddon", "inputstream.adaptive")
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
