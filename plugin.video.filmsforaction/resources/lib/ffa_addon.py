# -*- coding: utf-8 -*-

'''
   KODI Films For Action video add-on.
   Copyright (C) 2014 José Antonio Montes (jamontes)

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

   This is the first trial of the Films For Action video add-on for KODI.
   This add-on gets the videos from Films For Action web site and shows them properly ordered.
   You can choose the preferred language for the videos, if it is available.
   This plugin depends on the lutil library functions.
'''

from resources.lib.plugin import Plugin
import resources.lib.ffa_api as api

plugin_id = 'plugin.video.filmsforaction'

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

# By default, both, the website and the add-on are setup to show only the best videos.
all_filter = '&quality=all' if settings.getSetting("show_best") == "false" else '&quality=best'
sort_param = '&sort=new' if settings.getSetting("views") == "false" else '&sort=views'

if all_filter == '&quality=all':
    p.log("ffa.main: 'all videos' filter is explicit setup.")

if sort_param == '&sort=views':
    p.log("ffa.main: sorted by views is explicit setup.")

def get_located_string(string_name):
    return translation(localized_strings.get(string_name)) or string_name if string_name in localized_strings else string_name


# Entry point
def run():
    p.log("ffa.run")

    # Get params
    params = p.get_plugin_parms()

    action = params.get("action", '')
    if action:
        eval("%s(params)" % action)
    else:
        create_index(params)


# Main menu
def create_index(params):
    p.log("ffa.create_index "+repr(params))

    action = 'main_list'

    category_list = api.get_categories()

    menu_entry = get_located_string('All videos')
    all_videos_item = {
            'thumbnail': '',
            'info': {
                'title': menu_entry,
                'genre': menu_entry,
            },
            'path': p.get_plugin_path(url = 'https://www.filmsforaction.org/library/?category=all+videos' + all_filter + sort_param, action = action, category = menu_entry),
            'IsPlayable' : False
            }

    menu_entry = get_located_string('Search')
    search_videos_item = {
            'thumbnail': '',
            'info': {
                'title': menu_entry,
                'genre': menu_entry,
            },
            'path': p.get_plugin_path(action = 'search_videos', category = menu_entry),
            'IsPlayable' : False
            }

    categories = [ {
        'thumbnail': '',
        'info': {
            'title': category_title,
            'genre': category_title
        },
        'path': p.get_plugin_path(url = category_url + all_filter + sort_param, action = action, category = category_title),
        'IsPlayable' : False
        } for category_url, category_title in category_list]

    categories.insert(0, all_videos_item)
    categories.insert(0, search_videos_item)
    p.add_items(categories)


def main_list(params):
    p.log("ffa.main_list "+repr(params))

    category    = params.get("category", "")
    videos      = api.get_videolist(params.get("url"), category)
    reset_cache = 'yes' if params.get('reset_cache') == 'yes' or videos['reset_cache'] else 'no'

    video_list = [ {
        'thumbnail'   : video_entry.get('thumbnail') or '',
        'info': {
            'title'   : video_entry.get('title'),
            'plot'    : video_entry.get('plot')      or '',
            'studio'  : video_entry.get('credits')   or '',
            'genre'   : video_entry.get('genre')     or '',
            'rating'  : video_entry.get('rating')    or '',
            'duration': video_entry.get('duration')  or 1,
        },
        'path'        : p.get_plugin_path(
                            url         = video_entry['url'],
                            action      = 'play_video',
                        ) if video_entry['IsPlayable'] else p.get_plugin_path(
                            url         = video_entry['url'],
                            action      = 'main_list',
                            reset_cache = reset_cache,
                            category    = category,
                        ),
        'IsPlayable'  : video_entry['IsPlayable']
         }  for video_entry in videos['video_list']]

    p.add_items(video_list, reset_cache == 'yes')


def search_videos(params):
    p.log("ffa.search_video "+repr(params))

    search_string = p.get_keyboard_text(get_located_string('Search'))
    if search_string:
         params['url'] = api.get_search_url(search_string) + all_filter + sort_param
         p.log("ffa.search Value of search url: %s" % params['url'])
         return main_list(params)


def play_video(params):
    p.log("ffa.play_video "+repr(params))

    url = api.get_playable_url(params.get("url"))

    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Type not suported'))


