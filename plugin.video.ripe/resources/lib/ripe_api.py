# _*_ coding: utf-8 _*_

'''
   RIPE Meetings API lib: library functions for the RIPE Meetings add-on.
   Copyright (C) 2020 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Description:
   These funtions are called from the main plugin module, aimed to ease
   and simplify the add-on development process.
   Release 0.1.0
'''

import resources.lib.lutil as l

def set_debug(debug_flag, func_log=l.local_log):
    """This function is a wrapper to setup the debug flag into the lutil module"""
    l.set_debug_mode(debug_flag, func_log)


def get_events():
    """This function gest all the RIPE events from the RIPE website."""
    event_entry_sep       = '<div class="grid grid-flow-row'
    name_pattern          = '>(RIPE [^<]+)'
    event_pattern         = '([0-9]+)'
    site_pattern          = 'md:text-end">([^<]+)</span>'
    date_pattern          = '<time datetime="[-0-9]+">([^<]+)</time>'

    events_list = []
    last_page = False
    for page in range(1, 4):
        buffer_url = l.carga_web('https://www.ripe.net/meetings/ripe-meetings/archive/?page=%s' % page)
        for event_section in buffer_url.split(event_entry_sep)[1:]:
            event_name = l.find_first(event_section, name_pattern)
            ripe_event = l.find_first(event_name, event_pattern)
            if ripe_event == "60": # From this event to backwards there are no playable videos.
                last_page = True
                break # Into the presentations section.
            if ripe_event >= "91": # From this event onwards the URL changes.
                event_url = 'https://ripe%s.ripe.net/programme/meeting-plan/sessions/' % ripe_event
            else :
                event_url = 'https://ripe%s.ripe.net/archives/' % ripe_event

            site_name = l.find_first(event_section, site_pattern)
            dates_list = l.find_multiple(event_section, date_pattern)
            if len(dates_list) == 2:
                if dates_list[0][3:] == dates_list[1][3:]:
                    dates = '%s - %s' % (dates_list[0][:2], dates_list[1])
                else:
                    dates = '%s - %s' % (dates_list[0], dates_list[1])
            else:
                dates = ""

            event_title = '%s - %s (%s)' % (event_name, site_name, dates)
            l.log('event url: "%s" name: "%s" site: "%s" dates: "%s"' % (event_url, event_name, site_name, dates))
            events_list.append((event_url, event_title, site_name))

        if last_page:
            break # Stop loading more pages.

    return events_list


def get_videolist(url):
    """This function gets the video list from the RIPE website and returns them in a pretty data format."""

    if "meeting-plan" in url:
        return get_videolist_v2(url) # This URL contains the new webpage format and must be parsed in a different way.

    video_table_sep        = '<li><a href='
    video_url_pattern      = '"(.*?)"'
    root_url_pattern       = r'(https://ripe[0-9]+\.ripe\.net)'
    video_title_pattern    = '>(.*?)</a>'
    video_speaker_sep      = ' - '
    url_subpath            = '/archives/'
    fanart_pattern         = 'property="og:image" content="(.*?)"'
    fanart_pattern2        = ' src="([^"]+)" class="custom-logo"'
    fanart_pattern3        = 'img src="([^"]+)" alt='

    root_url = l.find_first(url, root_url_pattern)
    buffer_url = l.carga_web(url)

    fanart = l.find_first(buffer_url, fanart_pattern)
    if not fanart:
        fanart = l.find_first(buffer_url, fanart_pattern2)
    if not fanart:
        fanart = l.find_first(buffer_url, fanart_pattern3)
    if fanart.startswith("/"):
        fanart = root_url + fanart

    l.log('fanart url: "%s"' % fanart)

    video_list = []
    already_parsed = [] # Sometimes the videos are repeated into the list.
    for table_entry in buffer_url.split(video_table_sep)[1:]:
        video_url = l.find_first(table_entry, video_url_pattern)
        if not video_url or "video" not in video_url or video_url in already_parsed:
            continue
        already_parsed.append(video_url)
        if video_url.startswith("/"):
            video_url = root_url + video_url
        elif video_url.startswith("video"):
            video_url = root_url + url_subpath + video_url
        video_title = l.find_first(table_entry, video_title_pattern)
        title       = l.clean_title(video_title)
        speaker     = title.split(video_speaker_sep)[0]
        l.log('video_entry. title: "%s" url: "%s"' % (title, video_url))
        video_entry = {
            'url'        : video_url,
            'title'      : title,
            'plot'       : title,
            'year'       : '',
            'aired'      : '',
            'genre'      : '',
            'director'   : speaker,
            'writer'     : speaker,
            'studio'     : 'RIPE',
            'tagline'    : '',
            'credits'    : speaker,
            'showlink'   : '',
            'fanart'     : fanart,
            'thumbnail'  : fanart,
            'IsPlayable' : True,
            }
        video_list.append(video_entry)

    return video_list


def get_videolist_v2(url):
    """This function gets the video list from the RIPE website in the new format and returns them in a pretty data format."""
    video_table_sep        = '<h1>All sessions</h1>'
    video_section_sep      = '<li>'
    video_url_pattern      = '<a href="([^"]+)"><i [^>]+></i>Video</a>'
    video_title_pattern    = '<b><a href="[^"]+">(.*?)</a></b>'
    video_speaker_sec      = '<span>(.*?)</span>'
    video_speaker_pattern  = '<a href="[^"]+">(.*?)</a>'
    fanart_pattern         = '<img src="([^"]+)" '
    root_url_pattern       = r'(https://ripe[0-9]+\.ripe\.net)'

    root_url   = l.find_first(url, root_url_pattern)
    buffer_url = l.carga_web(url)
    fanart     = l.find_first(buffer_url, fanart_pattern)
    if fanart.startswith("/"):
        fanart = root_url + fanart

    l.log('fanart url: "%s"' % fanart)

    video_list     = []
    already_parsed = [] # Sometimes the videos are repeated into the list.
    video_sections = buffer_url.split(video_table_sep)[1]

    for video_section in video_sections.split(video_section_sep)[1:]:
        video_url = l.find_first(video_section, video_url_pattern)
        if not video_url or video_url in already_parsed:
            continue
        already_parsed.append(video_url)
        if video_url.startswith("/"):
            video_url = root_url + video_url
        video_title = l.find_first(video_section, video_title_pattern)
        title       = l.clean_title(video_title)
        speaker_sec = l.find_first(video_section, video_speaker_sec)
        speakers    = ""
        for i, speaker in enumerate(l.find_multiple(speaker_sec, video_speaker_pattern)):
            if i == 0:
                speakers = speaker
            else:
                speakers = '%s, %s' % (speakers, speaker)
        if speakers != "":
            title = '%s - %s' % (speakers, title)

        l.log('video_entry. title: "%s" url: "%s"' % (title, video_url))
        video_entry = {
            'url'        : video_url,
            'title'      : title,
            'plot'       : title,
            'year'       : '',
            'aired'      : '',
            'genre'      : '',
            'director'   : speakers,
            'writer'     : speakers,
            'studio'     : 'RIPE',
            'tagline'    : '',
            'credits'    : speakers,
            'showlink'   : '',
            'fanart'     : fanart,
            'thumbnail'  : fanart,
            'IsPlayable' : True,
            }
        video_list.append(video_entry)

    return video_list


def get_playable_url(url):
    """This function returns a playable URL fetching the video sources available"""
    video_url_pattern = '((?:/media/videos/|/archive/video/|/videos/).*?mp4)["\']'
    root_url_pattern  = r'(https://ripe[0-9]+\.ripe\.net)'

    if url.endswith('mp4'):
        # The URL is already playable.
        l.log('We have found this video_url with url "%s"' % url)
        return url

    root_url   = l.find_first(url, root_url_pattern)
    buffer_url = l.carga_web(url)
    video_link = l.find_first(buffer_url, video_url_pattern)
    if video_link:
        playable_url = root_url + video_link
        l.log('We have found this video_url "%s"' % playable_url)
    else:
        playable_url = ''
        l.log('We have not found any video for this url "%s"' % url)

    return playable_url
