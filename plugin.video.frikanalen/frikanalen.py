from __future__ import unicode_literals

import datetime
from requests import Session

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

    # NB: some fields have been skipped

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_response(r):
        return Video(
            description=r['description'],
            duration=r['duration'],
            header=r['header'],
            name=r['name'],
            ogv_url=r['ogv_url'],
            large_thumbnail_url=r['large_thumbnail_url'],
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
        return ScheduleItem(
            default_name=r['default_name'],
            video_id=r['video_id'],
            video=Video.from_response(r['video']),
            schedulereason=r['schedulereason'],
            starttime=datetime.datetime.strptime(r['starttime'], "%Y-%m-%dT%H:%M:%SZ"),
            duration=r['duration']
        )

def _get(path):
    r = session.get("https://frikanalen.no/api/" + path)
    r.raise_for_status()
    return r.json()


def is_today(t):
    return t.day == datetime.datetime.today().day


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
            print "> [{:d}:{:02d}] {:s} {:s}".format(t.hour, t.minute, item.video.name, item.duration)
        else:
            print "[{:d}:{:02d}] {:s} {:s}".format(t.hour, t.minute, item.video.name, item.duration)
    return ""
