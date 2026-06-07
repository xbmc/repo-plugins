# -*- coding: utf-8 -*-

'''
   KODI RNE Podcasts audio add-on.
   Copyright (C) 2015 José Antonio Montes (jamontes)

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

   This is the first trial of RNE Podcasts add-on for KODI.
   This add-on gets the audio podcasts from RNE web site and shows
   them properly ordered.
   This add-on depends on the lutil and plugin library functions.
'''

from resources.lib.plugin import Plugin
import resources.lib.rne_api as api

plugin_id = 'plugin.audio.rne'

localized_strings =  {
        'Next page'         : 30010,
        'Type not suported' : 30011,
        'Audio not located' : 30012,
        'Previous page'     : 30013,
        'Search'            : 30014,
        'Search result'     : 30015,
        }

p = Plugin(plugin_id)

settings = p.get_plugin_settings()
translation = p.get_plugin_translation()

debug_flag = settings.getSetting("debug") == "true"
all_programmes_flag = settings.getSetting("all_programmes") == "1"

p.set_debug_mode(debug_flag)
api.set_debug(debug_flag, p.log)

p.log("rne %s flag is set" % {True : 'all_the_programmes', False : 'only_emission'}[all_programmes_flag])


def get_located_string(string_name):
    """This function returns the localized string if it is available."""
    return translation(localized_strings.get(string_name)) or string_name if string_name in localized_strings else string_name


# Entry point
def run():
    """This function is the entry point to the add-on.
    It gets the add-on parameters and call the 'action' function.
    """
    p.log("rne.run")

    # Get the params
    params = p.get_plugin_parms()

    action = params.get("action", '')
    if action:
        eval("%s(params)" % action)
    else:
        menu_direct(params)


# Main menu
def create_index(params):
    """This function generates the main add-on menu, based on the website sections."""
    p.log("rne.create_index "+repr(params))

    menu_index = api.get_create_index()

    main_menu = [ {
            'thumbnail' : '',
            'info': {
                'title' : item.get('title'),
                'genre' : item.get('title'),
            },
            'path'      : p.get_plugin_path(
                action  = item.get('action'),
                url     = item.get('args'),
                genre   = item.get('title'),
            ),
            'IsPlayable': False,
            } for item in menu_index ]

    search_title = get_located_string('Search')
    search_menu  = {
            'thumbnail' : '',
            'info': {
                'title' : search_title,
                'genre' : search_title,
            },
            'path'      : p.get_plugin_path(
                action  = 'search_audio',
            ),
            'IsPlayable': False,
            }
    main_menu.append(search_menu)

    p.add_items(main_menu)


def program_list(params):
    """This function generates the programmes list, based on the upper menu selection."""
    p.log("rne.program_list "+repr(params))

    menu_url    = params.get('url')
    programs    = api.get_program_list(menu_url, all_programmes_flag, get_located_string)
    reset_cache = 'yes' if params.get('reset_cache') == 'yes' or programs.get('reset_cache') else 'no'

    main_menu = [ {
            'thumbnail'     : item.get('thumbnail', ''),
            'info': {
                'title'     : item.get('title',     ''),
                'genre'     : item.get('genre',     ''),
                'comment'   : item.get('comment',   ''),
            },
            'path'          : p.get_plugin_path(
                action      = item.get('action'),
                url         = item.get('url'),
                program     = item.get('program',   ''),
                canal       = item.get('canal',     ''),
                genre       = item.get('genre',     ''),
                reset_cache = reset_cache,
            ),
            'IsPlayable'    : False,
            } for item in programs.get('program_list') ]

    p.add_items(main_menu, reset_cache == 'yes')


def audio_list(params):
    """This function generates the podcasts list of the program emissions."""
    p.log("rne.audio_list "+repr(params))

    program     = params.get('program', '')
    canal       = params.get('canal',   '')
    genre       = params.get('genre',   '')

    audios      = api.get_audio_list(params.get('url'), get_located_string)
    reset_cache = 'yes' if params.get('reset_cache') == 'yes' or audios.get('reset_cache') else 'no'

    audio_items = [ {
        'thumbnail'     : '',
        'label'         : audio_entry.get('title',   ''),
        'info'          : {
            'title'     : audio_entry.get('title',   ''),
            'genre'     : genre,
            'album'     : canal,
            'artist'    : program,
            'comment'   : audio_entry.get('comment', ''),
            'year'      : audio_entry.get('year',     0),
            'duration'  : audio_entry.get('duration', 1),
            'rating'    : audio_entry.get('rating',   0),
        },
        'path'          : p.get_plugin_path(
            url         = audio_entry.get('url'),
            action      = audio_entry.get('action'),
        ) if audio_entry.get('IsPlayable') else p.get_plugin_path(
            url         = audio_entry.get('url'),
            action      = audio_entry.get('action'),
            program     = program,
            canal       = canal,
            genre       = genre,
            reset_cache = reset_cache,
        ),
        'IsPlayable'    : audio_entry.get('IsPlayable'),
        } for audio_entry in audios.get('audio_list') ]

    p.add_items(audio_items, reset_cache == 'yes')


def search_program(params):
    """This function gets the URL for search the podcast by title inside the program list."""
    p.log("rne.search_program "+repr(params))

    search_string = p.get_keyboard_text(get_located_string('Search'))
    if search_string:
         params['url'] = params.get('url') % search_string.replace(' ', '%20')
         params['search'] = search_string
         p.log("rne.search_program Value of search url: %s" % params['url'])
         return audio_list(params)


def menu_direct(params):
    """This funcion creates the menu for the direct channels play."""
    p.log("rne.menu_direct "+repr(params))

    channels = [ {
        'thumbnail'     : '',
        'label'         : channel.get('title', ''),
        'info'          : {
            'title'     : channel.get('title', ''),
        },
        'path'          : p.get_plugin_path(
            url         = channel.get('url'),
            action      = channel.get('action'),
        ),
        'IsPlayable'    : True,
        } for channel in api.get_direct_channels() ]

    p.add_items(channels)


def search_audio(params):
    """This function gets the URL for search the podcast emissions and list them if something is found on the website archives."""
    p.log("rne.search_audio "+repr(params))

    search_string = p.get_keyboard_text(get_located_string('Search'))
    if search_string:
         params['url'] = api.get_search_url(search_string)
         params['search'] = search_string
         p.log("rne.search Value of search url: %s" % params['url'])
         return search_list(params)


def search_list(params):
    """This function list the programs found by the website search engine"""
    p.log("rne.search_list "+repr(params))

    audios      = api.get_search_list(params.get('url'), get_located_string)
    reset_cache = 'yes' if params.get('reset_cache') == 'yes' or audios.get('reset_cache') else 'no'

    audio_items = [ {
        'thumbnail'     : '',
        'label'         : audio_entry.get('title',   ''),
        'info'          : {
            'title'     : audio_entry.get('title',   ''),
            'album'     : '"%s"' % params.get('search'),
            'artist'    : get_located_string('Search result'),
            'comment'   : audio_entry.get('comment', ''),
            'year'      : audio_entry.get('year',     0),
            'rating'    : 0,
        },
        'path'          : p.get_plugin_path(
            url         = audio_entry.get('url'),
            action      = audio_entry.get('action'),
        ) if audio_entry.get('IsPlayable') else p.get_plugin_path(
            url         = audio_entry.get('url'),
            action      = audio_entry.get('action'),
            search      = params.get('search'),
            reset_cache = reset_cache,
        ),
        'IsPlayable'    : audio_entry.get('IsPlayable'),
        } for audio_entry in audios.get('search_list') ]

    p.add_items(audio_items, reset_cache == 'yes')


def play_search(params):
    """This function plays the audio source from the search url link."""
    p.log("rne.play_search "+repr(params))

    url = api.get_playable_search_url(params.get("url"))

    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Audio not located'))


def play_audio(params):
    """This function plays the audio source."""
    p.log("rne.play_audio "+repr(params))

    url = params.get("url")

    if url.endswith('m3u'):
        url = api.get_playable_url(url)

    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Audio not located'))


