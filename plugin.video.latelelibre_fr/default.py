# -*- coding: utf-8 -*-

'''
   XBMC LaTeleLibre.fr video add-on.
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

   This is the first trial of LaTeleLibre.fr video add-on for XBMC.
   This add-on gets the videos from LaTeleLibre.fr web site and shows
   them properly ordered.
   This plugin depends on the lutil and plugin library functions.
'''

from resources.lib.plugin import Plugin
import resources.lib.ltl_api as api

plugin_id = 'plugin.video.latelelibre_fr'

localized_strings =  {
        'Next page'         : 30010,
        'Type not suported' : 30011,
        'Video not located' : 30012,
        'Previous page'     : 30013,
        'All videos'        : 30014,
        'Search'            : 30015,
        }

p = Plugin(plugin_id)

settings = p.get_plugin_settings()
translation = p.get_plugin_translation()

debug_flag = settings.getSetting("debug") == "true"

p.set_debug_mode(debug_flag)
api.set_debug(debug_flag, p.log)

st_release = settings.getSetting('version')
current_release = settings.getAddonInfo('version')
update_settings = False

# This is to make it sure that settings are correctly setup on every addon
# update if required or on first time of update settings either.
if not st_release:
    p.log("ltl Warning: First run of update settings.")
    settings.openSettings()
    settings.setSetting('version', current_release)
elif st_release != current_release:
    p.log("ltl Warning: updated release. Check for update settings.")
    if update_settings:
        settings.openSettings()
    settings.setSetting('version', current_release)

# Gets the quality for videos from settings
try:
    quality = int(settings.getSetting('quality'))
except:
    settings.setSetting('quality', '2') # Sets the default quality to 480
    quality = 2 # Default value is bandwith conservative.

p.log('ltl video quality setup to "%s"' % ('1080', '720', '480')[quality])
api.set_video_quality(quality)


def get_located_string(string_name):
    """This function returns the localized string if it is available."""
    return translation(localized_strings.get(string_name)).encode('utf-8') or string_name if string_name in localized_strings else string_name


# Entry point
def run():
    """This function is the entry point to the add-on.
    It gets the add-on parameters and call the 'action' function.
    """
    p.log("ltl.run")

    # Get the params
    params = p.get_plugin_parms()

    if params.get("action") is None:
        create_index(params)
    else:
        action = params.get("action")
        exec action+"(params)"


# Main menu
def create_index(params):
    """This function generates the main add-on menu, based on the website sections."""
    p.log("ltl.create_index "+repr(params))

    menu_index = api.get_create_index()

    main_menu = [ {
            'thumbnail' : '',
            'info': {
                'title' : item.get('title'),
                'genre' : item.get('title'),
            },
            'path'      : p.get_plugin_path(
                action  = item.get('action'),
                ctype   = item.get('ctype'),
                themes  = item.get('themes'),
                sorting = item.get('sorting'),
                title   = item.get('title'),
            ) if item.get('action') == 'menu_grille' else p.get_plugin_path(
                action  = item.get('action'),
                menus   = item.get('menus', 'no'),
            ),
            'IsPlayable': False,
            }  for item in menu_index]

    p.add_items(main_menu)


def menu_sec(params):
    """This function generates the menu entries for the Emissions, Chroniques, and Series sections."""
    p.log("ltl.menu_sec "+repr(params))

    root_url = 'http://latelelibre.fr'
    genre    = params.get('genre')
    menus    = params.get('menus')
    action   = 'video_sec'

    menu_sec = [ {
            'info': {
                'title'  : imenu.split('¿')[1],
                'genre'  : genre,
            },
            'path'       : p.get_plugin_path(
                url      = root_url + imenu.split('¿')[0],
                action   = action,
            ),
            'IsPlayable' : False,
            }  for imenu in menus.split('¡') ]

    p.add_items(menu_sec)


def video_sec(params):
    """This function list de videos for the Emissions, Chroniques, Series, and Search sections."""
    p.log("ltl.video_sec "+repr(params))

    video_list = api.get_video_sec(params.get('url'))

    video_items = [ {
        'thumbnail' : video_entry.get('thumbnail') or '',
        'info': {
            'title' : video_entry.get('title'),
            'plot'  : video_entry.get('plot')      or '',
            'studio': video_entry.get('credits')   or '',
            'genre' : video_entry.get('genre')     or '',
            'year'  : video_entry.get('year')      or '',
            'rating': video_entry.get('rating')    or '',
        },
        'path'      : p.get_plugin_path(
            url     = video_entry['url'],
            action  = 'play_video' if video_entry['IsPlayable'] else 'video_sec',
        ),
        'IsPlayable': video_entry['IsPlayable'],
        }  for video_entry in video_list]

    p.add_items(video_items)


def video_docs(params):
    """This function list the Documentary videos showed by the main page website."""
    p.log("ltl.video_docs "+repr(params))

    video_list = api.get_video_docs()
    action     = 'play_video'

    video_items = [ {
        'thumbnail'  : video_entry.get('thumbnail') or '',
        'info': {
            'title'  : video_entry.get('title'),
            'plot'   : video_entry.get('plot')      or '',
            'studio' : video_entry.get('credits')   or '',
            'genre'  : video_entry.get('genre')     or '',
            'year'   : video_entry.get('year')      or '',
            'rating' : video_entry.get('rating')    or '',
        },
        'path'       : p.get_plugin_path(
            url      = video_entry['url'],
            action   = action,
        ),
        'IsPlayable' : video_entry['IsPlayable'],
        }  for video_entry in video_list]

    p.add_items(video_items)


def menu_grille(params):
    """This function generates the Genres level menu for the 'All the Videos' and 'Reportages' sections."""
    p.log("ltl.menu_grille "+repr(params))

    ctype   = params.get('ctype')
    themes  = params.get('themes')
    sorting = params.get('sorting')
    genre   = params.get('title')
    action  = 'grille_sort'

    themes_items = [ {
        'info': {
            'title' : itheme.split('¿')[1],
            'genre' : genre,
        },
        'path'      : p.get_plugin_path(
            ctype   = ctype,
            sorting = sorting,
            action  = action,
            theme   = itheme.split('¿')[0],
            title   = genre,
        ),
        'IsPlayable': False,
        } for itheme in themes.split('¡') ]

    p.add_items(themes_items)


def grille_sort(params):
    """This function generates the 'Sorted by' level menu for the 'All the Videos' and 'Reportages' sections."""
    p.log("ltl.grille_sort "+repr(params))

    ctype   = params.get('ctype')
    theme   = params.get('theme')
    sorting = params.get('sorting')
    genre   = params.get('title')
    action  = 'grille_list'

    sorting_items = [ {
        'info': {
            'title' : isorting.split('¿')[1],
            'genre' : genre,
        },
        'path' : p.get_plugin_path(
            ctype   = ctype,
            sorting = isorting.split('¿')[0],
            action  = action,
            theme   = theme,
            genre   = genre,
        ),
        'IsPlayable': False,
        } for isorting in sorting.split('¡') ]

    p.add_items(sorting_items)


def grille_list(params):
    """This function list the videos for the 'All the Videos' and 'Reportages' sections."""
    p.log("ltl.grille_list "+repr(params))

    ctype   = params.get('ctype')
    theme   = params.get('theme')
    sorting = params.get('sorting')
    exclude = params.get('exclude', '')

    params_grille = {
        'type'    : ctype,
        'theme'   : theme,
        'sorting' : sorting,
        'exclude' : exclude,
        'limit'   : '15',
        }

    videos      = api.get_video_items(params=params_grille, localized=get_located_string)
    reset_cache = 'yes' if params.get('reset_cache') == 'yes' or videos['reset_cache'] else 'no'

    video_list = [ {
        'thumbnail'     : video_entry.get('thumbnail') or '',
        'info': {
            'title'     : video_entry.get('title'),
            'plot'      : video_entry.get('plot')      or '',
            'studio'    : video_entry.get('credits')   or '',
            'genre'     : video_entry.get('genre')     or '',
            'year'      : video_entry.get('year')      or '',
            'rating'    : video_entry.get('rating')    or '',
        },
        'path'          : p.get_plugin_path(
            url         = video_entry['url'],
            action      = 'play_video',
        ) if video_entry['IsPlayable'] else p.get_plugin_path(
            ctype       = video_entry['type'],
            theme       = video_entry['theme'],
            exclude     = video_entry['exclude'],
            sorting     = video_entry['sorting'],
            limit       = video_entry['limit'],
            action      = 'grille_list',
            reset_cache = reset_cache,
        ),
        'IsPlayable'    : video_entry['IsPlayable'],
        }  for video_entry in videos['video_list']]

    p.add_items(video_list, reset_cache == 'yes')


def search_videos(params):
    """This function gets the URL for search the videos and list them if something is found on the website archives."""
    p.log("ltl.search_video "+repr(params))

    search_string = p.get_keyboard_text(get_located_string('Search'))
    if search_string:
         params['url'] = api.get_search_url(search_string)
         p.log("ltl.search Value of search url: %s" % params['url'])
         return video_sec(params)


def play_video(params):
    """This function plays the videos if the hosted site of the video is supported."""
    p.log("ltl.play_video "+repr(params))

    url = api.get_playable_url(params.get("url"))
    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Type not suported'))


# Runs the add-on from here.
run()
