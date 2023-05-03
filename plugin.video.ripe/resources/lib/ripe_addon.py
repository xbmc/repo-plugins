# -*- coding: utf-8 -*-

'''
   KODI RIPE Meetings video add-on.
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

   This is the first trial of the RIPE Meetings video add-on for KODI.
   This add-on gets the videos from RIPE Meetings web sites and shows them properly ordered.
   This add-on depends on the lutil library functions.
'''

from resources.lib.plugin import Plugin
import resources.lib.ripe_api as api

plugin_id = 'plugin.video.ripe'

localized_strings =  {
        'Next page': 30010,
        'Type not suported': 30011,
        'Video not located': 30012,
        'Previous page': 30013,
        'All videos': 30014,
        'Search': 30015,
        }

p = Plugin(plugin_id)

settings = p.get_plugin_settings()
translation = p.get_plugin_translation()

debug_flag = settings.getSetting("debug") == "true"

p.set_debug_mode(debug_flag)
api.set_debug(debug_flag, p.log)

def get_located_string(string_name):
    return translation(localized_strings.get(string_name)).encode('utf-8') or string_name if string_name in localized_strings else string_name


# Entry point
def run():
    p.log("ripe.run")

    # Get params
    params = p.get_plugin_parms()

    action = params.get("action", '')
    if action == "main_list":
        main_list(params)
    elif action == "play_video":
        play_video(params)
    else:
        create_index(params)


# Main menu
def create_index(params):
    p.log("ripe.create_index "+repr(params))

    action = 'main_list'

    events_list = api.get_events()

    events = [ {
        'thumbnail': '',
        'info': {
            'title': event_title,
            'genre': event_title
        },
        'path': p.get_plugin_path(url = event_url, action = action, site = event_site),
        'IsPlayable' : False
        } for event_url, event_title, event_site in events_list]

    p.add_items(events)


def main_list(params):
    p.log("ripe.main_list "+repr(params))

    site        = params.get('site')
    videos      = api.get_videolist(params.get('url'))
    video_list = [ {
        'thumbnail'    : video_entry.get('thumbnail', ''),
        'fanart'       : video_entry.get('fanart', ''),
        'info': {
            'title'    : video_entry.get('title', ''),
            'plot'     : video_entry.get('plot', ''),
            'genre'    : video_entry.get('genre', ''),
            'year'     : video_entry.get('year', ''),
            'aired'    : video_entry.get('aired', ''),
            'director' : video_entry.get('director', ''),
            'writer'   : video_entry.get('writer', ''),
            'studio'   : video_entry.get('studio', ''),
            'tagline'  : video_entry.get('tagline', ''),
            'credits'  : video_entry.get('credits', ''),
            'showlink' : video_entry.get('showlink', ''),
            'country'  : site,

        },
        'path'         : p.get_plugin_path(
                            url         = video_entry.get('url'),
                            action      = 'play_video'
                       ),
        'IsPlayable'   : True
         } for video_entry in videos]

    p.add_items(video_list)


def play_video(params):
    p.log("ripe.play_video "+repr(params))

    url = api.get_playable_url(params.get("url"))

    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Type not suported'))
