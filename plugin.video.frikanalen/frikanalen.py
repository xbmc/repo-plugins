# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 Alexander Alemayhu
#               2018 Petter Reinholdtsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import unicode_literals

import datetime
from requests import Session
import urllib

session = Session()
session.headers['User-Agent'] = 'kodi.tv'
session.headers['app-version-android'] = '999'


def stream_url():
    return 'http://video.nuug.no/frikanalen.webm'


def stream_url_hd():
    return 'http://video.nuug.no/frikanalen-hd.webm'


class Video:
    id = None
    description = None
    duration = None
    header = None
    name = None
    ogv_url = None
    large_thumbnail_url = None
    organization = None
    categories = []

    # NB: some fields have been skipped

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_response(r):
        if 'header' in r and r['header'] is not None:
            r['header'] = r['header'] + "\n\nID #%s" % r['id']
        else:
            r['header'] = "ID #%s" % r['id']
        return Video(
            description=r['description'],
            duration=duration2sec(r['duration']),
            header=r['header'],
            name=r['name'],
            ogv_url=r['ogv_url'],
            large_thumbnail_url=r['large_thumbnail_url'],
            organization=r['organization'],
            categories=r['categories'],
        )


class ScheduleItem:
    # TODO: Review all properties
    default_name = None
    video_id = None
    video = None
    schedulereason = None
    starttime = None
    duration = None

    # NB: some fields have been skipped

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_response(r):
        if 'starttime' in r:
            starttime = iso2datetime(r['starttime'])
        else:
            starttime=None

        return ScheduleItem(
            default_name=r['default_name'],
            video_id=r['video_id'],
            video=Video.from_response(r['video']),
            schedulereason=r['schedulereason'],
            starttime=starttime,
            duration=duration2sec(r['duration']),
        )

def _get(path):
    r = session.get("https://frikanalen.no/api/" + path)
    r.raise_for_status()
    return r.json()


def is_today(t):
    return t.day == datetime.datetime.today().day


def videosearch(query):
    query= urllib.quote_plus(query)
    search_response = _get('videos/?has_tono_records=false&proper_import=true&publish_on_web=true&q=%s' % query)
    videos= [Video.from_response(item) for item in search_response['results']]
    return videos


def categories():
    categories_response = _get('categories/')
    return [item['name'] for item in categories_response['results']]


def in_category(category):
    category = urllib.quote_plus(category)
    category_response = _get('videos/?categories__name__icontains=%s&has_tono_records=false&proper_import=true&publish_on_web=true' % category)
    videos= [Video.from_response(item) for item in category_response['results']]
    return videos


def today_programs():
    schedule_response = _get('scheduleitems/?date=today')
    items = [ScheduleItem.from_response(item) for item in schedule_response['results']]
    return [item for item in items if is_today(item.starttime) == True]


def whats_on():
    now = datetime.datetime.now()
    program = sorted(today_programs())

    for item in program:
        t = item.starttime
        if t.hour == now.hour:
            print("> [{:d}:{:02d}] {:s} {:f}".format(t.hour, t.minute, item.video.name, item.duration))
        else:
            print("[{:d}:{:02d}] {:s} {:f}".format(t.hour, t.minute, item.video.name, item.duration))
    return ""

def iso2datetime(datestr):
    # Workaround for fractional seconds in the output
    if '+' in datestr:
        # FIXME this is a horrid way to handle timezones, simply throwing it away.
        datestr = datestr.split('+')[0]
        if '.' in datestr:
            return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")
    else:
        if '.' in datestr:
            return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            print("datestr=", datestr)
            return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%SZ")


def duration2sec(duration):
    """Convert duration on format H:M:S.frac to seconds"""
    p = duration.split(':')
    d = 0
    m = 1
    for part in p[::-1]:
        d = d + float(part) * m
        m = m * 60
    return d
