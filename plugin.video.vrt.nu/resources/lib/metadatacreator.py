# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implements a class for video metadata '''

from __future__ import absolute_import, division, unicode_literals


class MetadataCreator:
    ''' This class collects and creates an appropriate infoLabels dictionary for Kodi '''

    def __init__(self):
        ''' Initialize an empty Metadata object '''
        self.brands = []
        self.datetime = None
        self.duration = None
        self.episode = None
        self.geolocked = None
        self.mediatype = None
        self.offtime = None
        self.ontime = None
        self.permalink = None
        self.plot = None
        self.plotoutline = None
        self.season = None
        self.subtitle = None
        self.title = None
        self.tvshowtitle = None
        self.year = None

    def get_info_dict(self):
        ''' Return an infoLabels dictionary for Kodi '''
        from datetime import datetime
        import dateutil.tz
        from resources.lib import CHANNELS

        epoch = datetime.fromtimestamp(0, dateutil.tz.UTC)
        info_dict = dict()

        if self.brands:
            try:
                channel = next(c for c in CHANNELS if c.get('name') == self.brands[0])
                info_dict['studio'] = channel.get('studio')
            except StopIteration:
                # Retain original (unknown) brand, unless it is empty
                info_dict['studio'] = self.brands[0] or 'VRT'
        else:
            # No brands ? Use VRT instead
            info_dict['studio'] = 'VRT'

        if self.datetime:
            info_dict['aired'] = self.datetime.strftime('%Y-%m-%d %H:%M:%S')
            info_dict['date'] = self.datetime.strftime('%Y-%m-%d')
        elif self.ontime and self.ontime != epoch:
            info_dict['aired'] = self.ontime.strftime('%Y-%m-%d %H:%M:%S')
            info_dict['date'] = self.ontime.strftime('%Y-%m-%d')

        if self.ontime and self.ontime != epoch:
            info_dict['dateadded'] = self.ontime.strftime('%Y-%m-%d %H:%M:%S')
        elif self.datetime:
            info_dict['dateadded'] = self.datetime.strftime('%Y-%m-%d %H:%M:%S')

        if self.duration:
            info_dict['duration'] = self.duration

        if self.episode:
            info_dict['episode'] = self.episode

        # mediatype is one of: video, movie, tvshow, season, episode or musicvideo
        if self.mediatype:
            info_dict['mediatype'] = self.mediatype

        if self.permalink:
            info_dict['showlink'] = [self.permalink]

        if self.plot:
            info_dict['plot'] = self.plot.strip()

        if self.plotoutline:
            info_dict['plotoutline'] = self.plotoutline.strip()

        if self.season:
            try:
                info_dict['season'] = int(self.season)
            except ValueError:
                info_dict['season'] = self.season

        # NOTE: Does not seem to have any effect
        if self.subtitle:
            info_dict['tagline'] = self.subtitle

        if self.title:
            info_dict['title'] = self.title

        if self.tvshowtitle:
            info_dict['tvshowtitle'] = self.tvshowtitle
            info_dict['set'] = self.tvshowtitle

        if self.year:
            info_dict['year'] = self.year

        return info_dict
