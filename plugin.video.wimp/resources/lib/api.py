#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from datetime import date
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError
import simplejson


class NetworkError(Exception):
    pass


class WimpApi():

    API_URL = 'http://m.wimp.com/apiv2/'

    def get_current_videos(self):
        data = self.call('list')
        return self.__format_videos(data['videos'])

    def get_archive_dates(self):

        def month_range(start_month, start_year, end_month, end_year):
            ym_start = 12 * start_year + start_month - 1
            ym_end = 12 * end_year + end_month
            for ym in range(ym_start, ym_end):
                y, m = divmod(ym, 12)
                yield y, m + 1

        today = date.today()
        dates = month_range(12, 2008, today.month, today.year)
        return [{
            'title': date(year, month, 1).strftime('%B %Y'),
            'year': year,
            'month': month,
        } for year, month in dates]

    def get_archived_videos(self, year, month):
        params = {
            'year': '%04i' % year,
            'month': '%02i' % month,
        }
        data = self.call('archive', params)
        return self.__format_videos(data['videos'])

    def get_serch_result(self, search_string):
        params = {'query': search_string}
        data = self.call('search', params)
        return self.__format_videos(data['videos'])

    def __format_videos(self, videos):
        return [{
            'uid': video['uid'],
            'title': video['title'],
            'date': self.__format_date(video['date']),
            'page': video['page'],
            'thumb': video.get('thumb_506_332') or video.get('thumb_1164_766'),
            'video_url': video['video_hq_url'],
        } for video in videos]

    def __format_date(self, date_str):
        y, m, d = date_str.split('-')
        return '%02i.%02i.%s' % (int(d), int(m), int(y))

    def call(self, path, params=None):
        url = WimpApi.API_URL + path
        if params:
            url += '?' + urlencode(params)
        self.log('opening url: %s' % url)
        req = Request(url)
        req.add_header('User-Agent', 'XBMC WimpApi')
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError(error)
        except URLError, error:
            raise NetworkError(error)
        self.log('got %d bytes' % len(response))
        data = simplejson.loads(response)
        return data

    @staticmethod
    def log(text):
        print 'WimpApi: %s' % text


if __name__ == '__main__':
    api = WimpApi()
    assert api.get_current_videos()
    assert api.get_archived_videos(year=2012, month=9)
    assert api.get_archive_dates()
