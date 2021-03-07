from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from kodi_six import xbmcaddon
import re
from datetime import datetime
import time
import pytz
from tzlocal import get_localzone

UNIT_TEST = False

# Get Plug-In path
ADDON = xbmcaddon.Addon()
plugin_path = ADDON.getAddonInfo('path')
if (len(plugin_path) == 0):
    # Running under unit test
    UNIT_TEST = True


def to_local_time(timestamp):
    """ Convert from a UNIX timestamp to a valid date time """
    local_time = datetime.fromtimestamp(timestamp)
    return (local_time)


def get_episode_name(title, subtitle):
    """ Construct an episode name from the title and the subtitle"""
    if len(subtitle) == 0:
        subtitle = subtitle.replace("<p></p>", "")
        episode_name = '{0}'.format(title)
    else:
        title = title.replace("<p></p>", "")
        episode_name = '{0} - {1}'.format(title, subtitle)
    return (episode_name)


def get_top_stories_play_path(xmltext):
    """ Extracts the play path from a top story XML file """
    find = 'rtmp://flv.nhk.or.jp/ondemand/flv/nhkworld/upld/medias/en/news/(.+?)HQ'

    matches = re.compile(find).findall(xmltext)
    if len(matches) == 1:
        play_path = matches[0]
    else:
        play_path = None
    return play_path


def get_ataglance_play_path(xmltext):
    """ Extracts the play path from a At a Glance XML file """
    find = '<file.high>rtmp://flv.nhk.or.jp/ondemand/flv/nhkworld/english/news/ataglance/(.+?)</file.high>'

    matches = re.compile(find).findall(xmltext)
    if len(matches) == 1:
        play_path = matches[0]
    else:
        play_path = None
    return play_path


def get_news_program_play_path(xmltext):
    """ Extracts the play path from a news program file """
    find = 'rtmp://flv.nhk.or.jp/ondemand/flv/nhkworld/upld/medias/en/news/programs/(.+?)hq.mp4'

    matches = re.compile(find).findall(xmltext)
    if len(matches) == 1:
        play_path = matches[0]
    else:
        play_path = None
    return play_path


def get_schedule_title(start_date, end_date, title):
    """Returns a title formatted for a schedule (e.g. live stream, live)

    Arguments:
        start_date {datetime} -- Start date
        end_date {datetime} -- End date
        title {unicode} -- Title
     Returns:
        {unicode} -- 11:30-12:30: Journeys in Japan
    """
    return ('{0}-{1}: {2}'.format(start_date.strftime('%H:%M'),
                                  end_date.strftime('%H:%M'), title))


def get_timestamp_from_datestring(datestring):
    """Converts a news item date string into a NHK timestamp
    NHK Timestamp = Unix Timestamp * 1000

    Arguments:
        date_string {unicode} -- News item date string (e.g. '20200416130000')
     Returns:
        {unicode} -- NHK Timestamp (e.g. 1587008460000)
    """
    # Convert news date string to a Tokyo date
    tokyo = pytz.timezone('Asia/Tokyo')
    tokyo_dt = datetime(year=int(datestring[0:4]),
                        month=int(datestring[4:6]),
                        day=int(datestring[6:8]),
                        hour=int(datestring[8:10]),
                        minute=int(datestring[10:12]),
                        second=int(datestring[12:14]),
                        tzinfo=tokyo)
    # Convert to local time zone
    local_tz = get_localzone()
    local_dt = tokyo_dt.astimezone(local_tz)
    # Convert to NHK timestamp that can be used to populate
    # episode.broadcast_start_date etc.
    timestamp = int(time.mktime(local_dt.timetuple()) * 1000)
    return (timestamp)
