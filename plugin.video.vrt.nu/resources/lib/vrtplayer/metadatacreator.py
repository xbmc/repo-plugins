# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from datetime import datetime


class MetadataCreator:

    def __init__(self):
        self._title = None
        self._tvshowtitle = None
        self._duration = None
        self._plot = None
        self._plotoutline = None
        self._datetime = None
        self._season = None
        self._episode = None
        self._year = None
        self._mediatype = None
        self._url = None
        self._ontime = None
        self._offtime = None
        self._subtitle = None
        self._brands = None
        self._geolocked = None

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def subtitle(self):
        return self._subtitle

    @subtitle.setter
    def subtitle(self, value):
        self._subtitle = value

    @property
    def tvshowtitle(self):
        return self._tvshowtitle

    @tvshowtitle.setter
    def tvshowtitle(self, value):
        self._tvshowtitle = value

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, value):
        self._duration = value

    @property
    def plot(self):
        return self._plot

    @plot.setter
    def plot(self, value):
        self._plot = value.strip()

    @property
    def plotoutline(self):
        return self._plotoutline

    @plotoutline.setter
    def plotoutline(self, value):
        self._plotoutline = value.strip()

    @property
    def datetime(self):
        return self._datetime

    @datetime.setter
    def datetime(self, value):
        self._datetime = value

    @property
    def season(self):
        return self._season

    @season.setter
    def season(self, value):
        self._season = value

    @property
    def episode(self):
        return self._episode

    @episode.setter
    def episode(self, value):
        self._episode = value

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, value):
        self._year = value

    @property
    def mediatype(self):
        return self._mediatype

    @mediatype.setter
    def mediatype(self, value):
        self._mediatype = value

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def brands(self):
        return self._brands

    @brands.setter
    def brands(self, value):
        self._brands = value

    @property
    def ontime(self):
        return self._ontime

    @ontime.setter
    def ontime(self, value):
        self._ontime = value

    @property
    def offtime(self):
        return self._offtime

    @offtime.setter
    def offtime(self, value):
        self._offtime = value

    @property
    def geolocked(self):
        return self._geolocked

    @geolocked.setter
    def geolocked(self, value):
        self._geolocked = value

    def get_video_dict(self):
        video_dict = dict()

        if self.tvshowtitle:
            video_dict['tvshowtitle'] = self.tvshowtitle
            video_dict['set'] = self.tvshowtitle

        # NOTE: Does not seem to have any effect
        if self.subtitle:
            video_dict['tagline'] = self.subtitle

        if self.plot:
            video_dict['plot'] = self.plot

        if self.plotoutline:
            video_dict['plotoutline'] = self.plotoutline

        if self.duration:
            video_dict['duration'] = self.duration

        if self.season:
            video_dict['season'] = self.season

        if self.episode:
            video_dict['episode'] = self.episode

        if self.year:
            video_dict['year'] = self.year

        if self.mediatype:
            video_dict['mediatype'] = self.mediatype

        if self.datetime:
            video_dict['aired'] = self.datetime.strftime('%d.%m.%Y')
            video_dict['date'] = self.datetime.strftime('%d.%m.%Y')
        elif self.ontime and self.ontime != datetime(1970, 1, 1):
            video_dict['aired'] = self.ontime.strftime('%d.%m.%Y')
            video_dict['date'] = self.ontime.strftime('%d.%m.%Y')

        # NOTE: Does not seem to have any effect
        if self.ontime:
            video_dict['dateadded'] = self.ontime.strftime('%d.%m.%Y')
            video_dict['startdate'] = self.ontime.strftime('%d.%m.%Y')

        # NOTE/ Does not seem to have any effect
        if self.offtime:
            video_dict['enddate'] = self.offtime.strftime('%d.%m.%Y')

        # NOTE: Does not seem to have any effect
        if self.url:
            video_dict['path'] = self.url

        if self.brands:
            # NOTE: Does not seem to have any effect
            video_dict['channelname'] = self.brands[0] if isinstance(self.brands, list) else self.brands
            video_dict['studio'] = self.brands

        # rating
        # episodename
        # genre

        #if self.icon:
        #    video_dict['icon'] = self.icon
        #    video_dict['actualicon'] = self.icon

        # NOTE: Does not seem to have any effect
        if self.geolocked:
            video_dict['overlay'] = 7
            #video_dict['overlay'] = 'OverlayLocked.png'

        return video_dict
