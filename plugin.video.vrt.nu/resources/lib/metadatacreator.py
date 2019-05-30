# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals


class MetadataCreator:
    ''' This class collects and creates an appropriate infoLabels dictionary for Kodi '''

    def __init__(self):
        ''' Initialize an empty Metadata object '''
        self.brands = None
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

    def get_video_dict(self):
        ''' Return an infoLabels dictionary for Kodi '''
        from datetime import datetime
        import dateutil.tz
        from resources.lib import CHANNELS

        epoch = datetime.fromtimestamp(0, dateutil.tz.UTC)
        video_dict = dict()

        if self.brands:
            try:
                channel = next(c for c in CHANNELS if c.get('name') == self.brands[0])
                video_dict['studio'] = channel.get('studio')
            except StopIteration:
                # Retain original (unknown) brand, unless it is empty
                video_dict['studio'] = self.brands[0] or 'VRT'
        else:
            # No brands ? Use VRT instead
            video_dict['studio'] = 'VRT'

        if self.datetime:
            video_dict['aired'] = self.datetime.strftime('%Y-%m-%d %H:%M:%S')
            video_dict['date'] = self.datetime.strftime('%Y-%m-%d')
        elif self.ontime and self.ontime != epoch:
            video_dict['aired'] = self.ontime.strftime('%Y-%m-%d %H:%M:%S')
            video_dict['date'] = self.ontime.strftime('%Y-%m-%d')

        if self.ontime and self.ontime != epoch:
            video_dict['dateadded'] = self.ontime.strftime('%Y-%m-%d %H:%M:%S')
        elif self.datetime:
            video_dict['dateadded'] = self.datetime.strftime('%Y-%m-%d %H:%M:%S')

        if self.duration:
            video_dict['duration'] = self.duration

        if self.episode:
            video_dict['episode'] = self.episode

        # mediatype is one of: video, movie, tvshow, season, episode or musicvideo
        if self.mediatype:
            video_dict['mediatype'] = self.mediatype

        if self.permalink:
            video_dict['showlink'] = [self.permalink]

        if self.plot:
            video_dict['plot'] = self.plot.strip()

        if self.plotoutline:
            video_dict['plotoutline'] = self.plotoutline.strip()

        if self.season:
            video_dict['season'] = self.season

        # NOTE: Does not seem to have any effect
        if self.subtitle:
            video_dict['tagline'] = self.subtitle

        if self.title:
            video_dict['title'] = self.title

        if self.tvshowtitle:
            video_dict['tvshowtitle'] = self.tvshowtitle
            video_dict['set'] = self.tvshowtitle

        if self.year:
            video_dict['year'] = self.year

        return video_dict
