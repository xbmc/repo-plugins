# -*- coding: utf-8 -*-

# Copyright (C) 2018 Alexander Seiler
#
#
# This file is part of plugin.video.rtsplaytv.
#
# plugin.video.rtsplaytv is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plugin.video.rtsplaytv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plugin.video.rtsplaytv.
# If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import traceback

import datetime
import json
import socket
import urllib2
import urllib
import urlparse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon


from simplecache import SimpleCache

try:
    CompatStr = unicode  # Python2
except NameError:
    CompatStr = str  # Python3


def get_boolean_setting(label):
    """
    Retrieve the boolean value of a setting switch.

    Keyword arguments:
    label -- the settings label
    """
    return REAL_SETTINGS.getSetting(label) == 'true'


ADDON_ID = 'plugin.video.rtsplaytv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = REAL_SETTINGS.getAddonInfo('icon')
FANART = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE = REAL_SETTINGS.getLocalizedString
SEGMENTS = get_boolean_setting('Enable_Show_Segments')
SEGMENTS_TOPICS = get_boolean_setting('Enable_Settings_Topics')
PREFER_HD = get_boolean_setting('Prefer_HD')
SUBTITLES = get_boolean_setting('Extract_Subtitles')

PROFILE = xbmc.translatePath(
    REAL_SETTINGS.getAddonInfo('profile')).decode("utf-8")

BU = 'rts'
HOST_URL = 'https://www.rts.ch'
TIMEOUT = 30
CONTENT_TYPE = 'videos'
DEBUG = get_boolean_setting('Enable_Debugging')
NUMBER_OF_EPISODES = 10

FAVOURITE_SHOWS_FILENAME = 'favourite_shows.json'
TODAY = LANGUAGE(30058)
YESTERDAY = LANGUAGE(30059)
WEEKDAYS = (LANGUAGE(30060), LANGUAGE(30061), LANGUAGE(30062), LANGUAGE(30063),
            LANGUAGE(30064), LANGUAGE(30065), LANGUAGE(30066))
IDREGEX = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d+'

socket.setdefaulttimeout(TIMEOUT)


# General helper functions:

def log(msg, level=xbmc.LOGDEBUG):
    """
    Logs a message using Kodi's logging interface.

    Keyword arguments:
    msg   -- the message to log
    level -- the logging level
    """
    if DEBUG:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)


def get_params():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))


def str_or_none(inp, default=None):
    """
    Convert an input to a string (if possible), otherwise
    return a default value.

    Keyword arguments:
    inp     -- input
    default -- the default value to return (default: None)
    """
    if inp is None:
        return default
    try:
        return CompatStr(inp, 'utf-8')
    except TypeError:
        return inp


def float_or_none(val, scale=1, invscale=1, default=None):
    """
    Convert an input value to a float (if possible), otherwise
    return a default value.

    Keyword arguments:
    val      -- input value
    scale    -- divide the input by this value (default: 1)
    invscale -- multiply the input by this value (default: 1)
    default  -- the default return value (default: None)
    """
    if val == '':
        val = None
    if val is None:
        return default
    try:
        return float(val) * float(invscale) / float(scale)
    except ValueError:
        return default


def int_or_none(val, scale=1, invscale=1, default=None):
    """
    Convert an input value to an integer (if possible), otherwise
    return a default value.

    Keyword arguments:
    val      -- input value
    scale    -- divide the input by this value (default: 1)
    invscale -- multiply the input by this value (default: 1)
    default  -- the default return value (default: None)
    """
    if val == '':
        val = None
    if val is None:
        return default
    try:
        return int(val) * invscale // scale
    except ValueError:
        return default


def assemble_query_string(query_list):
    """
    Assembles a query for an URL and returns the assembled query string.

    Keyword arguments:
    query_list -- a list of queries
    """
    return '&'.join(['{}={}'.format(k, v) for (k, v) in query_list])


def get_duration(duration_string):
    """
    Converts a duration string into an integer respresenting the
    total duration in seconds. There are three possible input string
    forms possible, either
    <hours>:<minutes>:<seconds>
    or
    <minutes>:<seconds>
    or
    <seconds>
    In case of failure a NoneType will be returned.

    Keyword arguments:
    duration_string -- a string of the above Form.
    """
    if not isinstance(duration_string, CompatStr):
        return None
    durrex = r'(((?P<hour>\d+):)?(?P<minute>\d+):)?(?P<second>\d+)'
    match = re.match(durrex, duration_string)
    if match:
        hour = int(match.group('hour')) if match.group('hour') else 0
        minute = int(match.group('minute')) if match.group('minute') else 0
        second = int(match.group('second'))
        return 60 * 60 * hour + 60 * minute + second
    log('Cannot convert duration string: &s' % duration_string)
    return None


def parse_datetime(input_string):
    """
    Tries to create a datetime object from a given input string. There are
    several different forms of input strings supported, for more details
    have a look in the documentations of the called functions. In case
    of failure, a NoneType will be returned.

    Keyword arguments:
    input_string -- a string to convert into a datetime object
    """
    # input_string = str(input_string)
    # print(input_string)
    date_time = _parse_weekday_time(input_string)
    if date_time:
        return date_time
    date_time = _parse_date_time(input_string)
    if date_time:
        return date_time
    date_time = _parse_date_time_tz(input_string)
    if not date_time:
        log('parse_datetime: Could not parse input string %s', input_string)
    return date_time


def _parse_date_time_tz(input_string):
    """
    Creates a datetime object from a string of the form
    %Y-%m-%dT%H:%M:%S<tz>
    where <tz> represents the timezone info and is of the form
    (+|-)%H:%M.
    A NoneType will be returned in the case where it was not possible
    to create a datetime object.

    Keyword arguments:
    input_string -- a string of the above form
    """
    dt_regex = r'''(?x)
                    (?P<dt>
                        \d{4}-\d{2}-\d{2}T\d{2}(:|h)\d{2}:\d{2}
                    )
                    (?P<tz>
                        [-+]\d{2}(:|h)\d{2}
                    )
                '''
    match = re.match(dt_regex, input_string)
    if match:
        dts = match.group('dt')
        # We ignore timezone information for now
        try:
            # Strange behavior of strptime in Kodi?
            # dt = datetime.datetime.strptime(dts, '%Y-%m-%dT%H:%M:%S')
            # results in a TypeError in some cases...
            year = int(dts[0:4])
            month = int(dts[5:7])
            day = int(dts[8:10])
            hour = int(dts[11:13])
            minute = int(dts[14:16])
            second = int(dts[17:19])
            date_time = datetime.datetime(
                year, month, day, hour, minute, second)
            return date_time
        except ValueError:
            return None
    return None


def _parse_weekday_time(input_string):
    """
    Creates a datetime object from a string of the form
    <weekday>,? %H:%M(:S)?
    where <weekday> is either a german name of a weekday
    ('Montag', 'Dienstag', ...) or 'gestern', 'heute', 'morgen'.
    If it is not possible to create a datetime object from
    the given input string, a NoneType will be returned.

    Keyword arguments:
    input_string -- a string of the above form
    """
    log('_parse_weekday_time, input_string = %s' % input_string)
    if BU == 'srf':
        weekdays = (
            'Montag',
            'Dienstag',
            'Mittwoch',
            'Donnerstag',
            'Freitag',
            'Samstag',
            'Sonntag',
        )
        special_weekdays = ('gestern', 'heute', 'morgen')
    else: # BU == 'rts'
        weekdays = (
            'Lundi',
            'Mardi',
            'Mercredi',
            'Jeudi',
            'Vendredi',
            'Samedi',
            'Dimanche',
        )
        special_weekdays = ('hier', 'aujourd\'hui', 'demain')
    weekdays += special_weekdays

    recent_date_regex = r'''(?x)
                            (?P<weekday>[a-zA-z]+)
                            \s*,\s*
                            (?P<hour>\d{2})(:|h)
                            (?P<minute>\d{2})
                            (:
                                (?P<second>\d{2})
                            )?
                        '''
    recent_date_match = re.match(recent_date_regex, input_string)
    if recent_date_match:
        # This depends on correct date settings in Kodi...
        today = datetime.date.today()
        # wdl = [x for x in weekdays if input_string.startswith(x)]
        wdl = [x for x in weekdays if re.match(x, input_string, re.IGNORECASE)]
        if not wdl:
            return None
        index = weekdays.index(wdl[0])
        if index == 9:  # tomorrow
            offset = datetime.timedelta(1)
        elif index == 8:  # today
            offset = datetime.timedelta(0)
        elif index == 7:  # yesterday
            offset = datetime.timedelta(-1)
        else:  # Monday, Tuesday, ..., Sunday
            days_off_pos = (today.weekday() - index) % 7
            offset = datetime.timedelta(-days_off_pos)
        try:
            hour = int(recent_date_match.group('hour'))
            minute = int(recent_date_match.group('minute'))
            time = datetime.time(hour, minute)
        except ValueError:
            return None
        try:
            second = int(recent_date_match.group('second'))
            time = datetime.time(hour, minute, second)
        except (ValueError, TypeError):
            pass
        date_time = datetime.datetime.combine(today, time) + offset
    else:
        return None
    return date_time


def _parse_date_time(input_string):
    """
    Creates a datetime object from a string of the following form:
    %d.%m.%Y,? %H:%M(:%S)?

    Note that the delimiter between the date and the time is optional, and also
    the seconds in the time are optional.

    If the given string cannot be transformed into a appropriate datetime
    object, a NoneType will be returned.

    Keyword arguments:
    input_string -- the date and time in the above form
    """
    full_date_regex = r'''(?x)
                        (?P<day>\d{2})\.
                        (?P<month>\d{2})\.
                        (?P<year>\d{4})
                        \s*,?\s*
                        (?P<hour>\d{2})(:|h)
                        (?P<minute>\d{2})
                        (:
                            (?P<second>\d{2})
                        )?
                    '''
    full_date_match = re.match(full_date_regex, input_string)
    if full_date_match:
        try:
            year = int(full_date_match.group('year'))
            month = int(full_date_match.group('month'))
            day = int(full_date_match.group('day'))
            hour = int(full_date_match.group('hour'))
            minute = int(full_date_match.group('minute'))
            date_time = datetime.datetime(year, month, day, hour, minute)
        except ValueError:
            return None
        try:
            second = int(full_date_match.group('second'))
            date_time = datetime.datetime(
                year, month, day, hour, minute, second)
            return date_time
        except (ValueError, TypeError):
            return date_time
    return None


class RTSPlayTV(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()

    @staticmethod
    def build_url(mode=None, name=None, url=None, page_hash=None, page=None):
        """Build a URL for this Kodi plugin.

        Keyword arguments:
        mode      -- an integer representing the mode
        name      -- a string containing some information, e.g. a video id
        url       -- a plugin URL, if another plugin/script needs to called
        page_hash -- a string (used to get additional videos through the API)
        page      -- an integer used to indicate the current page in
                     the list of items
        """
        if mode:
            mode = str(mode)
        if page:
            page = str(page)
        added = False
        queries = (url, mode, name, page_hash, page)
        query_names = ('url', 'mode', 'name', 'page_hash', 'page')
        purl = sys.argv[0]
        for query, qname in zip(queries, query_names):
            if query:
                add = '?' if not added else '&'
                purl += '%s%s=%s' % (add, qname, urllib.quote_plus(query))
                added = True
        return purl

    def open_url(self, url, use_cache=True):
        """Open and read the content given by a URL.

        Keyword arguments:
        url       -- the URL to open as a string
        use_cache -- boolean to indicate if the cache provided by the
                     Kodi module SimpleCache should be used (default: True)
        """
        log('open_url, url = ' + str(url))
        try:
            cache_response = None
            if use_cache:
                cache_response = self.cache.get(
                    ADDON_NAME + '.openURL, url = %s' % url)
            if not cache_response:
                request = urllib2.Request(url)
                request.add_header(
                    'User-Agent',
                    ('Mozilla/5.0 (X11; Linux x86_64; rv:59.0)'
                     'Gecko/20100101 Firefox/59.0'))
                response = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(
                    ADDON_NAME + '.openURL, url = %s' % url,
                    response,
                    expiration=datetime.timedelta(hours=2))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s' % url)
        except urllib2.URLError as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
        except socket.timeout as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
        except Exception as err:
            log("openURL Failed! " + str(err), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                ADDON_NAME, LANGUAGE(30100), ICON, 4000)
            return ''

    def extract_id_list(self, url):
        """
        Opens a webpage and extracts video ids (of the form "id": "<vid>")
        from JavaScript snippets.

        Keyword argmuents:
        url -- the URL of the webpage
        """
        log('extract_id_list, url = %s' % url)
        response = self.open_url(url)
        string_response = str_or_none(response, default='')
        if not string_response:
            log('No video ids found on %s' % url)
        readable_string_response = string_response.replace('&quot;', '"')
        id_regex = r'''(?x)
                        \"id\"
                        \s*:\s*
                        \"
                        (?P<id>
                            %s
                        )
                        \"
                    ''' % IDREGEX
        id_list = [m.group('id') for m in re.finditer(
            id_regex, readable_string_response)]
        return id_list

    @staticmethod
    def read_favourite_show_ids():
        """
        Reads the show ids from the file defined by the global
        variable FAVOURITE_SHOWS_FILENAMES and returns a list
        containing these ids.
        An empty list will be returned in case of failure.
        """
        file_path = os.path.join(PROFILE, FAVOURITE_SHOWS_FILENAME)
        try:
            with open(file_path, 'r') as f:
                json_file = json.load(f)
                try:
                    return [entry['id'] for entry in json_file]
                except KeyError:
                    log('Unexpected file structure for %s.' %
                        FAVOURITE_SHOWS_FILENAME)
                    return []
        except (IOError, TypeError):
            return []

    @staticmethod
    def write_favourite_show_ids(show_ids):
        """
        Writes a list of show ids to the file defined by the global
        variable FAVOURITE_SHOWS_FILENAME.

        Keyword arguments:
        show_ids -- a list of show ids (as strings)
        """
        show_ids_dict_list = [{'id': show_id} for show_id in show_ids]
        file_path = os.path.join(PROFILE, FAVOURITE_SHOWS_FILENAME)
        if not os.path.exists(PROFILE):
            os.makedirs(PROFILE)
        with open(file_path, 'w') as f:
            json.dump(show_ids_dict_list, f)

    def build_main_menu(self):
        """
        Builds the main menu of the plugin:

        All shows
        Favourite shows
        Newest favourite shows
        Recommendations
        Newest shows (by topic)
        Most clicked shows (by topic)
        Shows by date
        Live TV
        RTS.ch live
        """
        log('build_main_menu')
        main_menu_list = [
            {
                # All shows
                'name': LANGUAGE(30050),
                'mode': 10,
                'isFolder': True,
                'displayItem': get_boolean_setting('All_Shows')
            }, {
                # Favourite shows
                'name': LANGUAGE(30051),
                'mode': 11,
                'isFolder': True,
                'displayItem': get_boolean_setting('Favourite_Shows')
            }, {
                # Newest favourite shows
                'name': LANGUAGE(30052),
                'mode': 12,
                'isFolder': True,
                'displayItem': get_boolean_setting('Newest_Favourite_Shows')
            }, {
                # Recommendations
                'name': LANGUAGE(30053),
                'mode': 16,
                'isFolder': True,
                'displayItem': get_boolean_setting('Recommendations')
            }, {
                # Newest shows
                'name': LANGUAGE(30054),
                'mode': 13,
                'isFolder': True,
                'displayItem': get_boolean_setting('Newest_Shows')
            }, {
                # Most clicked shows
                'name': LANGUAGE(30055),
                'mode': 14,
                'isFolder': True,
                'displayItem': get_boolean_setting('Most_Clicked_Shows')
            }, {
                # Shows by date
                'name': LANGUAGE(30057),
                'mode': 17,
                'isFolder': True,
                'displayItem': get_boolean_setting('Shows_By_Date')
            }, {
                # Live TV
                'name': LANGUAGE(30072),
                'mode': 26,
                'isFolder': True,
                'displayItem': get_boolean_setting('Live_TV')
            }, {
                # RTS.ch live
                'name': LANGUAGE(30070),
                'mode': 18,
                'isFolder': True,
                'displayItem': get_boolean_setting('RTS_Live')
            }
        ]
        for menu_item in main_menu_list:
            if menu_item['displayItem']:
                list_item = xbmcgui.ListItem(menu_item['name'])
                list_item.setProperty('IsPlayable', 'false')
                list_item.setArt({'thumb': ICON})
                purl = self.build_url(
                    mode=menu_item['mode'], name=menu_item['name'])
                xbmcplugin.addDirectoryItem(
                    handle=int(sys.argv[1]), url=purl,
                    listitem=list_item, isFolder=menu_item['isFolder'])

    def build_dates_overview_menu(self):
        """
        Builds the menu containing the folders for episodes of
        the last 10 days.
        """
        log('build_dates_overview_menu')

        def folder_name(dato):
            """
            Generates a Kodi folder name from an date object.

            Keyword arguments:
            dato -- a date object
            """
            today = datetime.date.today()
            if dato == today:
                name = TODAY
            elif dato == today + datetime.timedelta(-1):
                name = YESTERDAY
            else:
                name = '%s, %s' % (WEEKDAYS[dato.weekday()],
                                   dato.strftime('%d.%m.%Y'))
            return name

        current_date = datetime.date.today()
        number_of_days = 7

        for i in range(number_of_days):
            dato = current_date + datetime.timedelta(-i)
            list_item = xbmcgui.ListItem(label=folder_name(dato))
            list_item.setArt({'thumb': ICON})
            name = dato.strftime('%d-%m-%Y')
            purl = self.build_url(mode=24, name=name)
            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]), url=purl,
                listitem=list_item, isFolder=True)

        choose_item = xbmcgui.ListItem(label=LANGUAGE(30071))
        choose_item.setArt({'thumb': ICON})
        purl = self.build_url(mode=25)
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]), url=purl,
            listitem=choose_item, isFolder=True)

    def pick_date(self):
        """
        Opens a date choosing dialog and lets the user input a date.
        Redirects to the date menu of the chosen date.
        In case of failure or abortion redirects to the date
        overview menu.
        """
        date_picker = xbmcgui.Dialog().numeric(1, LANGUAGE(30071), None)
        if date_picker is not None:
            date_elems = date_picker.split('/')
            try:
                day = int(date_elems[0])
                month = int(date_elems[1])
                year = int(date_elems[2])
                chosen_date = datetime.date(year, month, day)
                name = chosen_date.strftime('%d-%m-%Y')
                self.build_date_menu(name)
            except (ValueError, IndexError):
                log('pick_date: Invalid date chosen.')
                self.build_dates_overview_menu()
        else:
            self.build_dates_overview_menu()

    def build_date_menu(self, date_string):
        """
        Builds a list of episodes of a given date.

        Keyword arguments:
        date_string -- a string representing date in the form %d-%m-%Y,
                       e.g. 12-03-2017
        """
        log('build_date_menu, date_string = %s' % date_string)

        url = HOST_URL + '/play/tv/programDay/%s' % date_string
        id_list = self.extract_id_list(url)

        for vid in id_list:
            self.build_episode_menu(
                vid, include_segments=False, segment_option=SEGMENTS)

    def build_topics_overview_menu(self, newest_or_most_clicked):
        """
        Builds a list of folders, where each folders represents a
        topic (e.g. News).

        Keyword arguments:
        newest_or_most_clicked -- a string (either 'Newest' or 'Most clicked')
        """
        log('build_topics_overview_menu, newest_or_most_clicked = %s' %
            newest_or_most_clicked)
        if newest_or_most_clicked == 'Newest':
            mode = 22
        elif newest_or_most_clicked == 'Most clicked':
            mode = 23
        else:
            log('build_topics_overview_menu: Unknown mode, \
                must be "Newest" or "Most clicked".')
            return
        topics_url = HOST_URL + '/play/tv/topicList'
        log('build_topics_overview_menu: Read URL: %s' % topics_url)
        topics_json = json.loads(self.open_url(topics_url))
        if not isinstance(topics_json, list) or not topics_json:
            log('No topics found.')
            return
        for elem in topics_json:
            list_item = xbmcgui.ListItem(label=elem.get('title'))
            list_item.setProperty('IsPlayable', 'false')
            list_item.setArt({'thumb': ICON})
            name = elem.get('id')
            if name:
                purl = self.build_url(mode=mode, name=name)
                xbmcplugin.addDirectoryItem(
                    handle=int(sys.argv[1]), url=purl,
                    listitem=list_item, isFolder=True)

    def build_topics_menu(self, name, topic_id=None, page=1):
        """
        Builds a list of videos (can also be folders) for a given topic.

        Keyword arguments:
        name     -- the type of the list, can be 'Newest', 'Most clicked',
                    'Soon offline' or 'Trending'.
        topic_id -- the topic id for the given topic, this is only needed
                    for the types 'Newest' and 'Most clicked' (default: None)
        page     -- an integer representing the current page in the list
        """
        log('build_topics_menu, name = %s, topic_id = %s, page = %s' %
            (name, topic_id, page))
        number_of_videos = 50
        if name == 'Newest':
            url = '%s/play/tv/topic/%s/latest?numberOfVideos=%s' % (
                HOST_URL, topic_id, number_of_videos)
            mode = 22
        elif name == 'Most clicked':
            url = '%s/play/tv/topic/%s/mostClicked?numberOfVideos=%s' % (
                HOST_URL, topic_id, number_of_videos)
            mode = 23
        elif name == 'Soon offline':
            url = '%s/play/tv/videos/soon-offline-videos?numberOfVideos=%s' % (
                HOST_URL, number_of_videos)
            mode = 15
        elif name == 'Trending':
            url = ('%s/play/tv/videos/trending?numberOfVideos=%s'
                   '&onlyEpisodes=true&includeEditorialPicks=true') % (
                       HOST_URL, number_of_videos)
            mode = 16
        else:
            log('build_topics_menu: Unknown mode.')
            return

        log('build_topics_menu. URL = %s' % url)
        id_list = self.extract_id_list(url)
        try:
            page = int(page)
        except TypeError:
            page = 1

        reduced_id_list = id_list[(page - 1) * NUMBER_OF_EPISODES:
                                  page * NUMBER_OF_EPISODES]
        for vid in reduced_id_list:
            self.build_episode_menu(vid, include_segments=False)

        try:
            vid = id_list[page*NUMBER_OF_EPISODES]
            next_item = xbmcgui.ListItem(label=LANGUAGE(30073))
            next_item.setProperty('IsPlayable', 'false')
            name = topic_id if topic_id else ''
            purl = self.build_url(mode=mode, name=name, page=page+1)
            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]), url=purl,
                listitem=next_item, isFolder=True)
        except IndexError:
            return

    def build_favourite_shows_menu(self):
        """
        Builds a list of folders for the favourite shows.
        """
        log('build_favourite_shows_menu')
        favourite_show_ids = self.read_favourite_show_ids()
        self.build_all_shows_menu(favids=favourite_show_ids)

    def build_newest_favourite_menu(self, page=1):
        """
        Builds a Kodi list of the newest favourite shows.

        Keyword arguments:
        page -- an integer indicating the current page on the
                list (default: 1)
        """
        log('build_newest_favourite_menu')
        number_of_days = 30
        show_ids = self.read_favourite_show_ids()

        # TODO: This depends on the local time settings
        now = datetime.datetime.now()
        current_month_date = datetime.date.today().strftime('%m-%Y')
        list_of_episodes_dict = []
        banners = {}
        for sid in show_ids:
            json_url = ('%s/play/tv/show/%s/latestEpisodes?numberOfEpisodes=%d'
                        '&tillMonth=%s') % (HOST_URL, sid, number_of_days,
                                            current_month_date)
            log('build_newest_favourite_menu. Open URL %s.' % json_url)
            response = json.loads(self.open_url(json_url))
            try:
                banner_image = str_or_none(
                    response['show']['bannerImageUrl'], default='')
                if banner_image.endswith('/3x1'):
                    banner_image += '/scale/width/1000'
            except KeyError:
                banner_image = None

            episode_list = response.get('episodes', [])
            for episode in episode_list:
                date_time = parse_datetime(
                    str_or_none(episode.get('date'), default=''))
                if date_time and \
                        date_time >= now + datetime.timedelta(-number_of_days):
                    list_of_episodes_dict.append(episode)
                    banners.update({episode.get('id'): banner_image})
        sorted_list_of_episodes_dict = sorted(
            list_of_episodes_dict, key=lambda k: parse_datetime(
                str_or_none(k.get('date'), default='')), reverse=True)
        try:
            page = int(page)
        except TypeError:
            page = 1
        reduced_list = sorted_list_of_episodes_dict[
            (page - 1) * NUMBER_OF_EPISODES:page * NUMBER_OF_EPISODES]
        for episode in reduced_list:
            segments = episode.get('segments', [])
            is_folder = True if segments and SEGMENTS else False
            self.build_entry(
                episode, banner=banners.get(episode.get('id')),
                is_folder=is_folder)

        if len(sorted_list_of_episodes_dict) > page * NUMBER_OF_EPISODES:
            next_item = xbmcgui.ListItem(label=LANGUAGE(30073))
            next_item.setProperty('IsPlayable', 'false')
            purl = self.build_url(mode=12, page=page+1)
            xbmcplugin.addDirectoryItem(
                int(sys.argv[1]), purl, next_item, isFolder=True)

    def read_all_available_shows(self):
        """
        Downloads a list of all available shows and returns this list.
        """
        log('read_all_available_shows')
        json_url = ('http://il.srgssr.ch/integrationlayer/1.0/ue/%s/tv/'
                    'assetGroup/editorialPlayerAlphabetical.json') % BU
        log('read_all_available_shows. Open URL %s' % json_url)
        json_response = json.loads(self.open_url(json_url))
        try:
            show_list = json_response['AssetGroups']['Show']
        except KeyError:
            log('read_all_available_shows: No shows found.')
            return []
        if not isinstance(show_list, list) or not show_list:
            log('read_all_available_shows: No shows found.')
            return []
        return show_list

    def manage_favourite_shows(self):
        """
        Opens a Kodi multiselect dialog to let the user choose
        his/her personal favourite show list.
        """
        log('manage_favourite_shows')
        show_list = self.read_all_available_shows()
        stored_favids = self.read_favourite_show_ids()
        names = [x['title'] for x in show_list]
        ids = [x['id'] for x in show_list]

        preselect_inds = []
        for stored_id in stored_favids:
            try:
                preselect_inds.append(ids.index(stored_id))
            except ValueError:
                pass
        ancient_ids = [x for x in stored_favids if x not in ids]

        dialog = xbmcgui.Dialog()
        selected_inds = dialog.multiselect(
            LANGUAGE(30069), names, preselect=preselect_inds)

        if selected_inds is not None:
            new_favids = [ids[ind] for ind in selected_inds]
            # Keep the old show ids:
            new_favids += ancient_ids

            self.write_favourite_show_ids(new_favids)

    def build_all_shows_menu(self, favids=None):
        """
        Builds a list of folders containing the names of all the current
        shows.

        Keyword arguments:
        favids -- A list of show ids (strings) respresenting the favourite
                  shows. If such a list is provided, only the folders for
                  the shows on that list will be build. (default: None)
        """
        log('build_all_shows_menu')
        show_list = self.read_all_available_shows()

        list_items = []
        for jse in show_list:
            try:
                title = str_or_none(jse['title'])
                show_id = str_or_none(jse['id'])
            except KeyError:
                log('build_all_shows_menu: Skipping, no title or id found.')
                continue

            # Skip if we build the 'favourite show menu' and the current
            # show id is not in our favourites:
            if favids is not None and show_id not in favids:
                continue

            list_item = xbmcgui.ListItem(label=title)
            list_item.setProperty('IsPlayable', 'false')
            list_item.setInfo(
                'video',
                {
                    'title': title,
                    'plot': str_or_none(jse.get('lead')),
                }
            )

            try:
                image_url = str_or_none(
                    jse['Image']['ImageRepresentations']
                    ['ImageRepresentation'][0]['url'])
                thumbnail = image_url + '/scale/width/668'\
                    if image_url else ICON
                banner = image_url.replace(
                    'WEBVISUAL', 'HEADER_RTS_PLAYER') if image_url else None
            except (KeyError, IndexError):
                image_url = FANART
                thumbnail = ICON

            list_item.setArt({
                'thumb': thumbnail,
                'poster': image_url,
                'banner': banner,
            })
            url = self.build_url(mode=20, name=show_id)
            list_items.append((url, list_item, True))
        xbmcplugin.addDirectoryItems(
            int(sys.argv[1]), list_items, totalItems=len(list_items))

    def build_tv_menu(self):
        """
        Builds the overview over the RTS TV channels.
        """
        overview_url = 'https://www.rts.ch/play/tv/live/overview'
        overview_json = json.loads(
            self.open_url(overview_url, use_cache=False))
        urns = [x['urn'] for x in overview_json['teaser']]
        for urn in urns:
            json_url = ('https://il.srgssr.ch/integrationlayer/2.0/'
                        'mediaComposition/byUrn/%s.json') % urn
            info_json = json.loads(self.open_url(json_url, use_cache=False))
            try:
                json_entry = info_json['chapterList'][0]
            except (KeyError, IndexError):
                log('build_tv_menu: Unexpected json structure for element %s'
                    % urn)
                continue
            self.build_entry(json_entry)

    def play_livestream(self, stream_url):
        """
        Plays a livestream, given a unauthenticated stream url.

        Keyword arguments:
        stream_url -- the stream url
        """
        auth_url = self.get_auth_url(stream_url)
        play_item = xbmcgui.ListItem('Live', path=auth_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)

    def build_show_menu(self, show_id, page_hash=None):
        """
        Builds a list of videos (can be folders in case of segmented videos)
        for a show given by its show id.

        Keyword arguments:
        show_id   -- the id of the show
        page_hash -- the page hash to get the list of
                     another page (default: None)
        """
        log('build_show_menu, show_id = %s, page_hash=%s' % (show_id,
                                                             page_hash))
        # TODO: This depends on the local time settings
        current_month_date = datetime.date.today().strftime('%m-%Y')
        if not page_hash:
            json_url = ('%s/play/tv/show/%s/latestEpisodes?numberOfEpisodes=%d'
                        '&tillMonth=%s') % (HOST_URL, show_id,
                                            NUMBER_OF_EPISODES,
                                            current_month_date)
        else:
            json_url = ('%s/play/tv/show/%s/latestEpisodes?nextPageHash=%s'
                        '&tillMonth=%s') % (HOST_URL, show_id, page_hash,
                                            current_month_date)
        log('build_show_menu. Open URL %s' % json_url)
        json_response = json.loads(self.open_url(json_url))

        try:
            banner_image = str_or_none(
                json_response['show']['bannerImageUrl'], default='')
            if banner_image.endswith('/3x1'):
                banner_image += '/scale/width/1000'
        except KeyError:
            banner_image = None

        next_page_hash = None
        if 'nextPageUrl' in json_response:
            next_page_url = str_or_none(
                json_response.get('nextPageUrl'), default='')
            next_page_hash_regex = r'nextPageHash=(?P<hash>[0-9a-f]+)'
            match = re.search(next_page_hash_regex, next_page_url)
            if match:
                next_page_hash = match.group('hash')

        json_episode_list = json_response.get('episodes', [])
        if not json_episode_list:
            log('No episodes for show %s found.' % show_id)
            return

        for episode_entry in json_episode_list:
            segments = episode_entry.get('segments', [])
            enable_segments = True if SEGMENTS and segments else False
            self.build_entry(
                episode_entry, banner=banner_image, is_folder=enable_segments)

        if next_page_hash and page_hash != next_page_hash:
            log('page_hash: %s' % page_hash)
            log('next_hash: %s' % next_page_hash)
            next_item = xbmcgui.ListItem(label=LANGUAGE(30073))
            next_item.setProperty('IsPlayable', 'false')
            url = self.build_url(
                mode=20, name=show_id, page_hash=next_page_hash)
            xbmcplugin.addDirectoryItem(
                int(sys.argv[1]), url, next_item, isFolder=True)

    def build_episode_menu(self, video_id, include_segments=True,
                           segment_option=SEGMENTS_TOPICS):
        """
        Builds a list entry for a episode by a given video id.
        The segment entries for that episode can be included too.
        The video id can be an id of a segment. In this case an
        entry for the segment will be created.

        Keyword arguments:
        video_id         -- the id of the video
        include_segments -- indicates if the segments (if available) of the
                            video should be included in the list
                            (default: True)
        segment_option   -- which segment option to use
                            (default: SEGMENTS_TOPCICS)
        """
        log('build_episode_menu, video_id = %s, include_segments = %s' %
            (video_id, include_segments))
        json_url = ('https://il.srgssr.ch/integrationlayer/2.0/%s/'
                    'mediaComposition/video/%s.json') % (BU, video_id)
        log('build_episode_menu. Open URL %s' % json_url)
        try:
            json_response = json.loads(self.open_url(json_url))
        except Exception:
            log('build_episode_menu: Cannot open media json for %s.'
                % video_id)
            return

        chapter_urn = json_response.get('chapterUrn', '')
        segment_urn = json_response.get('segmentUrn', '')

        id_regex = r'[a-z]+:[a-z]+:[a-z]+:(?P<id>.+)'
        match_chapter_id = re.match(id_regex, chapter_urn)
        match_segment_id = re.match(id_regex, segment_urn)
        chapter_id = match_chapter_id.group('id') if match_chapter_id else None
        segment_id = match_segment_id.group('id') if match_segment_id else None

        if not chapter_id:
            log('build_episode_menu: No valid chapter URN \
                available for video_id %s' % video_id)
            return

        try:
            banner = str_or_none(
                json_response['show']['bannerImageUrl'], default='')
            if banner.endswith('/3x1'):
                banner += '/scale/width/1000'
        except KeyError:
            banner = None

        json_chapter_list = json_response.get('chapterList', [])
        json_chapter = None
        for chapter in json_chapter_list:
            if chapter.get('id') == chapter_id:
                json_chapter = chapter
                break
        if not json_chapter:
            log('build_episode_menu: No chapter ID found \
                for video_id %s' % video_id)
            return

        json_segment_list = json_chapter.get('segmentList', [])
        if video_id == chapter_id:
            if include_segments:
                self.build_entry(json_chapter, banner)
                for segment in json_segment_list:
                    self.build_entry(segment, banner)
            else:
                if segment_option and json_segment_list:
                    self.build_entry(json_chapter, banner, is_folder=True)
                else:
                    self.build_entry(json_chapter, banner)
        else:
            json_segment = None
            for segment in json_segment_list:
                if segment.get('id') == segment_id:
                    json_segment = segment
                    break
            if not json_segment:
                log('build_episode_menu: No segment ID found \
                    for video_id %s' % video_id)
                return
            self.build_entry(json_segment, banner)

    def build_entry(self, json_entry, banner=None, is_folder=False):
        """
        Builds an list item for a video or folder by giving the json part,
        describing this video.

        Keyword arguments:
        json_entry -- the part of the json describing the video
        banner     -- URL of the show's banner (default: None)
        is_folder  -- indicates if the item is a folder (default: False)
        """
        log('build_entry')
        title = json_entry.get('title')
        vid = json_entry.get('id')
        description = json_entry.get('description')

        image = json_entry.get('imageUrl', '')
        # RTS image links have a strange appendix '/16x9'.
        # This needs to be removed from the URL:
        image = image.strip('/16x9')

        duration = int_or_none(json_entry.get('duration'), scale=1000)
        if not duration:
            duration = get_duration(json_entry.get('duration'))
        date_string = str_or_none(json_entry.get('date'), default='')
        dto = parse_datetime(date_string)
        kodi_date_string = dto.strftime('%Y-%m-%d') if dto else None

        list_item = xbmcgui.ListItem(label=title)
        list_item.setInfo(
            'video',
            {
                'title': title,
                'plot': description,
                'duration': duration,
                'aired': kodi_date_string,
            }
        )
        list_item.setArt({
            'thumb': image,
            'poster': image,
            'banner': banner,
        })
        subs = json_entry.get('subtitleList', [])
        if subs and SUBTITLES:
            subtitle_list = [x.get('url') for x in subs if
                             x.get('format') == 'VTT']
            if not subtitle_list:
                log('No WEBVTT subtitles found for video id %s.' % vid)
            list_item.setSubtitles(subtitle_list)
        if is_folder:
            list_item.setProperty('IsPlayable', 'false')
            url = self.build_url(mode=21, name=vid)
        else:
            list_item.setProperty('IsPlayable', 'true')
            url = self.build_url(mode=50, name=vid)
        xbmcplugin.addDirectoryItem(
            int(sys.argv[1]), url, list_item, isFolder=is_folder)

    def get_auth_url(self, url, segment_data=None):
        """
        Returns the authenticated URL from a given stream URL.

        Keyword arguments:
        url -- a given stream URL
        """
        log('get_auth_url, url = %s' % url)
        spl = urlparse.urlparse(url).path.split('/')
        token = json.loads(
            self.open_url(
                'http://tp.srgssr.ch/akahd/token?acl=/%s/%s/*' %
                (spl[1], spl[2]), use_cache=False)) or {}
        auth_params = token.get('token', {}).get('authparams')
        if segment_data:
            # timestep_string = self._get_timestep_token(segment_data)
            # url += ('?' if '?' not in url else '&') + timestep_string
            pass
        if auth_params:
            url += ('?' if '?' not in url else '&') + auth_params
        return url

    def play_video(self, video_id):
        """
        Gets the video stream information of a video and starts to play it.

        Keyword arguments:
        video_id -- the video of the video to play
        """
        log('play_video, video_id = %s' % video_id)
        json_url = ('https://il.srgssr.ch/integrationlayer/2.0/%s/'
                    'mediaComposition/video/%s.json') % (BU, video_id)
        log('play_video. Open URL %s' % json_url)
        json_response = json.loads(self.open_url(json_url))

        chapter_list = json_response.get('chapterList', [])
        if not chapter_list:
            log('play_video: no stream URL found.')
            return

        first_chapter = chapter_list[0]
        resource_list = first_chapter.get('resourceList', [])
        if not resource_list:
            log('play_video: no stream URL found.')
            return

        stream_urls = {
            'SD': '',
            'HD': '',
        }
        for resource in resource_list:
            if resource.get('protocol') == 'HLS':
                for key in ('SD', 'HD'):
                    if resource.get('quality') == key:
                        stream_urls[key] = resource.get('url')

        if not stream_urls['SD'] and not stream_urls['HD']:
            log('play_video: no stream URL found.')
            return

        stream_url = stream_urls['HD'] if (stream_urls['HD'] and PREFER_HD)\
            or not stream_urls['SD'] else stream_urls['SD']
        log('play_video, stream_url = %s' % stream_url)
        auth_url = self.get_auth_url(stream_url)

        start_time = end_time = None
        if 'segmentUrn' in json_response:  # video_id is the ID of a segment
            segment_list = first_chapter.get('segmentList', [])
            for segment in segment_list:
                if segment.get('id') == video_id:
                    start_time = float_or_none(
                        segment.get('markIn'), scale=1000)
                    end_time = float_or_none(
                        segment.get('markOut'), scale=1000)
                    break

            if start_time and end_time:
                parsed_url = urlparse.urlparse(auth_url)
                query_list = urlparse.parse_qsl(parsed_url.query)
                updated_query_list = []
                for query in query_list:
                    if query[0] == 'start' or query[0] == 'end':
                        continue
                    updated_query_list.append(query)
                updated_query_list.append(('start', CompatStr(start_time)))
                updated_query_list.append(('end', CompatStr(end_time)))
                new_query = assemble_query_string(updated_query_list)
                surl_result = urlparse.ParseResult(
                    parsed_url.scheme, parsed_url.netloc,
                    parsed_url.path, parsed_url.params,
                    new_query, parsed_url.fragment)
                auth_url = surl_result.geturl()
        log('play_video, auth_url = %s' % auth_url)
        play_item = xbmcgui.ListItem(video_id, path=auth_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, play_item)


def run():
    """
    Run the plugin.
    """
    params = get_params()
    try:
        url = urllib.unquote_plus(params["url"])
    except Exception:
        url = None
    try:
        name = urllib.unquote_plus(params["name"])
    except Exception:
        name = None
    try:
        mode = int(params["mode"])
    except Exception:
        mode = None
    try:
        page_hash = urllib.unquote_plus(params['page_hash'])
    except Exception:
        page_hash = None
    try:
        page = urllib.unquote_plus(params['page'])
    except Exception:
        page = None

    log("Mode: "+str(mode))
    log("URL : "+str(url))
    log("Name: "+str(name))

    if mode is None:
        RTSPlayTV().build_main_menu()
    elif mode == 10:
        RTSPlayTV().build_all_shows_menu()
    elif mode == 11:
        RTSPlayTV().build_favourite_shows_menu()
    elif mode == 12:
        RTSPlayTV().build_newest_favourite_menu(page=page)
    elif mode == 13:
        RTSPlayTV().build_topics_overview_menu('Newest')
    elif mode == 14:
        RTSPlayTV().build_topics_overview_menu('Most clicked')
    elif mode == 16:
        RTSPlayTV().build_topics_menu('Trending', page=page)
    elif mode == 17:
        RTSPlayTV().build_dates_overview_menu()
    elif mode == 19:
        RTSPlayTV().manage_favourite_shows()
    elif mode == 20:
        RTSPlayTV().build_show_menu(name, page_hash=page_hash)
    elif mode == 21:
        RTSPlayTV().build_episode_menu(name)
    elif mode == 22:
        RTSPlayTV().build_topics_menu('Newest', name, page=page)
    elif mode == 23:
        RTSPlayTV().build_topics_menu('Most clicked', name, page=page)
    elif mode == 24:
        RTSPlayTV().build_date_menu(name)
    elif mode == 25:
        RTSPlayTV().pick_date()
    elif mode == 26:
        RTSPlayTV().build_tv_menu()
    elif mode == 50:
        RTSPlayTV().play_video(name)
    elif mode == 51:
        RTSPlayTV().play_livestream(name)

    xbmcplugin.setContent(int(sys.argv[1]), CONTENT_TYPE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
