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
    event_entry_sep       = '<tr>'
    event_section_sep     = '<td>'
    event_pattern         = '(ripe[0-9]+)'
    name_pattern          = '>(RIPE [^<]+)'
    field_pattern         = '<p data-block-key="[^"]+">([^<]+)</p>'

    buffer_url = l.carga_web("https://www.ripe.net/membership/meetings/ripe-meetings/archive")
    events_list = []
    names_list = []
    for event_section in buffer_url.split(event_entry_sep)[2:]:
        ripe_event = l.find_first(event_section, event_pattern)
        if ripe_event == "ripe60": # From this event to backwards there are no playable videos
            break                  # into the presentations section.
        event_url = 'https://%s.ripe.net/archives/' % ripe_event
        event_name = l.find_first(event_section, name_pattern)
        names_list.append(event_name)
        section_fields = event_section.split(event_section_sep)
        if len(section_fields) == 4:
            site_name = l.find_first(section_fields[2], field_pattern)
            dates = l.find_first(section_fields[3], field_pattern)
        else:
            site_name = ""
            dates = ""

        event_title = '%s - %s (%s)' % (event_name, site_name, dates)
        l.log('event url: "%s" name: "%s" site: "%s" dates: "%s"' % (event_url, event_name, site_name, dates))
        events_list.append((event_url, event_title, site_name))

    return events_list


def get_videolist(url):
    """This function gets the video list from the RIPE website and returns them in a pretty data format."""
    video_table_sep        = '<li><a href='
    video_url_pattern      = '"(.*?)"'
    root_url_pattern       = '(https://ripe[0-9]+\.ripe\.net)'
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


def get_playable_url(url):
    """This function returns a playable URL fetching the video sources available"""
    video_url_pattern = '(/archive/video/.*?mp4)["\']'
    video_url_altpatt = '(/videos/.*?mp4)["\']'
    root_url_pattern  = '(https://ripe[0-9]+\.ripe\.net)'

    if url.endswith('mp4'):
        # The URL is already playable.
        l.log('We have found this video_url with url "%s"' % url)
        return url

    root_url     = l.find_first(url, root_url_pattern)

    buffer_url = l.carga_web(url)
    video_link = l.find_first(buffer_url, video_url_pattern)
    if video_link:
        playable_url = root_url + video_link
        l.log('We have found this video_url with url_pattern1 "%s"' % playable_url)
    else:
        video_link = l.find_first(buffer_url, video_url_altpatt)
        if video_link:
            playable_url = root_url + video_link
            l.log('We have found this video_url with alternative pattern  "%s"' % playable_url)
        else:
            playable_url = ''
            l.log('We have not found any video for this url "%s"' % url)

    return playable_url
