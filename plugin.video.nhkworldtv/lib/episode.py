from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import object
from kodi_six import xbmcgui, xbmc
from . import utils, url
from . import kodiutils
from datetime import datetime


class Episode(object):
    """ NHK Episode that contains all the necessary information
    to convert itself into a Kodi ListItem"""
    def __init__(self):
        """ Creates an Episode instance """
        self.vod_id = None
        self.pgm_no = None
        self.title = None
        self._plot = None
        self.plot_include_time_difference = False
        """ Optional: Include time difference (3 minutes ago) in the Plot
        """
        self.plot_include_broadcast_detail = False
        """ Optional: Include broadcast detail (available until) in the Plot
        """
        self._duration = None
        self.aspect = None
        self.width = None
        self.height = None
        self.url = None
        self.is_playable = False
        self.playcount = None
        self._date = None
        self._aired = None
        self._year = None
        self._broadcast_start_date = None
        self._broadcast_end_date = None
        self._thumb = None
        self._fanart = None
        self._video_info = None
        self.bandwidth = 0
        """ Optional: Set Internet Bandwidth Restriction
        """
        self._cast = None
        self._kodi_list_item = xbmcgui.ListItem
        self.absolute_image_url = False
        self.from_cache = False

    #
    # Properties
    #

    @property
    def duration(self):
        """ Gets the duration info label """
        if (self._duration is not None):
            return self._duration
        elif ((self.broadcast_start_date is not None)
              and (self.broadcast_end_date is not None)):
            duration = self.broadcast_end_date - self.broadcast_start_date
            return duration.seconds

    @duration.setter
    def duration(self, value):
        """ Sets the duration info label """
        self._duration = value

    @property
    def plot(self):
        """ Gets the plot info label """
        return self._plot

    @plot.setter
    def plot(self, value):
        """ Sets the plot info label """
        self._plot = value

    @property
    def broadcast_start_date(self):
        """ Gets the current broadcast start date in local timezone """
        return self._broadcast_start_date

    @broadcast_start_date.setter
    def broadcast_start_date(self, value):
        """ Sets the current broadcast start date from the timestamp value """
        if (value is None):
            self._broadcast_start_date = None
            self._date = None
            self._aired = None
        else:
            timestamp = int(value) // 1000
            local_date = utils.to_local_time(timestamp)
            self._broadcast_start_date = local_date
            self._date = local_date
            self._aired = local_date

    @property
    def broadcast_end_date(self):
        """ Gets the current broadcast end date in local timezone """
        return self._broadcast_end_date

    @broadcast_end_date.setter
    def broadcast_end_date(self, value):
        """ Sets the current broadcast end date from the timestamp value """
        if (value is None):
            self._broadcast_end_date = None
        else:
            timestamp = int(value) // 1000
            local_date = utils.to_local_time(timestamp)
            self._broadcast_end_date = local_date

    @property
    def thumb(self):
        """ Gets the thumbnail URL """
        return self._thumb

    @thumb.setter
    def thumb(self, value):
        """ Sets thumbnail URL """
        if ('/nhkworld/' in value and not self.absolute_image_url):
            self._thumb = url.get_nhk_website_url(value)
        else:
            self._thumb = value

    @property
    def fanart(self):
        """ Gets the fanart URL """
        return self._fanart

    @fanart.setter
    def fanart(self, value):
        """ Sets thumbnail URL """
        if ('/nhkworld/' in value and not self.absolute_image_url):
            self._fanart = url.get_nhk_website_url(value)
        else:
            self._fanart = value

    @property
    def date(self):
        """ Get the sort date
        Date Format: 01.01.2009
        """
        if (self._date is not None):
            return self._date.strftime('%d.%m.%Y')
        else:
            return None

    @property
    def aired(self):
        """ Get the aired date
        Date Format: 2008-12-07
        """
        if (self._aired is not None):
            return self._aired.strftime('%Y-%m-%d')
        else:
            return None

    @property
    def year(self):
        if (self._date is not None):
            self._year = self._date.strftime('%Y')
            return self._year
        else:
            return None

    @property
    def video_info(self):
        if (self._video_info is not None):
            return self._video_info
        elif (self.aspect is not None):
            vi = {
                'aspect': self.aspect,
                'width': self.width,
                'height': self.height
            }
            self._video_info = vi
            return vi

        else:
            return None

    @video_info.setter
    def video_info(self, value):
        """ Sets a Kodi Video Info """
        self._video_info = value

    @property
    def kodi_list_item(self):
        """ Gets the current Kodi List Item """

        if (self.url is not None):
            # Path was provided - created the ListItem with path
            li = xbmcgui.ListItem(path=self.url, offscreen=True)
            li.setLabel(self.title)
        else:
            # Create ListItem with title
            li = xbmcgui.ListItem(self.title, offscreen=True)

        li.setArt({'thumb': self.thumb, 'fanart': self.fanart})
        li.setLabel(self.title)

        # Get info label
        info_label = self.get_info_label()

        if (self.is_playable):
            # Playable episode
            li.setProperty('IsPlayable', 'true')
            info_label['mediatype'] = 'episode'
            li.setMimeType('application/x-mpegURL')
            li.setContentLookup(False)

        # Only add Stream Info if the the video_info property is not none
        if (self.video_info is not None):
            li.addStreamInfo('video', self.video_info)

        # Set the info label
        li.setInfo('video', info_label)
        self._kodi_list_item = li
        xbmc.log('Created list item: {0}'.format(self.title))
        return self._kodi_list_item

    #
    # Methods
    #

    def get_info_label(self):
        """ Create the InfoLabel from the Episode properties

        Returns:
            dict -- Dictionary with the Info Label properties
        """

        info_label = {}

        if (self.plot_include_time_difference is True):
            # Include time difference in plot
            info_label['Plot'] = '{0}\n\n{1}'.format(
                self.get_time_difference(), self.plot)
        elif (self.plot_include_broadcast_detail
              and self.broadcast_end_date is not None):
            # Include broadcast detail if there is an endDate
            info_label['Plot'] = kodiutils.get_string(30050).format(
                self.plot, self.broadcast_end_date.strftime('%Y-%m-%d'))
        else:
            info_label['Plot'] = self.plot

        info_label['Title'] = self.title

        if (self.duration is not None):
            info_label['Duration'] = self.duration

        if (self.pgm_no is not None):
            info_label['Episode'] = self.pgm_no

        if (self.year is not None):
            info_label['Year'] = self.year

        if (self._date is not None):
            info_label['date'] = self.date

        if (self._aired is not None):
            info_label['aired'] = self.aired

        if (self.playcount is not None):
            info_label['playcount'] = self.playcount

        return (info_label)

    def get_time_difference(self, compare_date=datetime.now()):
        """Get the time difference between the
        Start date and the compare_date

        Mirrors the behaviour from the NHK Website

        Arguments:
            compare_date {datetime} -- Date to compare with
            must be be newer than start_date

        Returns:
            {unicode} -- e.g 9 hours ago or 25.01.2020
        """
        date_delta = compare_date - self.broadcast_start_date
        date_delta_minutes = date_delta.seconds // 60
        date_delta_hours = date_delta_minutes // 60
        if (date_delta.days > 0):
            # Show as absolute date
            time_difference = self.broadcast_start_date.strftime(
                '%A, %b %d, %H:%M')
        elif (date_delta_hours < 1):
            # Show in minutes
            time_difference = kodiutils.get_string(30062).format(
                date_delta_minutes)
        elif (date_delta_hours == 1):
            # Show as hour
            time_difference = kodiutils.get_string(30060).format(
                date_delta_hours)
        else:
            # Show as hours (plural)
            time_difference = kodiutils.get_string(30061).format(
                date_delta_hours)
        return (time_difference)
