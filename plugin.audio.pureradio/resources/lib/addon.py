# -*- coding: utf-8 -*-

'''
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

'''

from resources.lib.plugin import Plugin
import resources.lib.api as api

plugin_id = 'plugin.audio.pureradio'

p = Plugin(plugin_id)

settings = p.get_plugin_settings()
translation = p.get_plugin_translation()

localized_strings =  {
        'Play'     : 30001,
        'Podcasts' : 30002,
}

# Entry point
def run():
    """This function is the entry point to the add-on.
    It gets the add-on parameters and call the 'action' function.
    """
    p.log("pureradio.run")
    # Get the params
    params = p.get_plugin_parms()
    action = params.get("action", '')
    # changed this to static function calls
    if (action == 'play_audio'):
        play_audio(params)
    elif (action == 'retrieve_podcasts'):
        retrieve_podcasts(params)
    else:
        create_index(params)    # default menu

# Main menu
def create_index(params):
    """This function creates the main menu."""
    main_menu = [
        {'thumbnail': '', 
            'info': {'type':'Audio', 
            'title': get_located_string("Play")}, 
            'path': p.get_plugin_path(action='play_audio', url=settings.getSetting('stream_url')),
            'IsPlayable': True, },
        {'thumbnail': '', 
            'info': {'title': get_located_string("Podcasts")}, 
            'path': p.get_plugin_path(action='retrieve_podcasts', url=settings.getSetting('podcast_url')),
            'IsPlayable': False, }
    ]    
    p.add_items(main_menu)

def retrieve_podcasts(params):
    """This function retrieves the podcasts on spreaker."""
    p.log("pureradio.retrieve_podcasts "+repr(params))    
    url = params.get("url")    
    if url:
        create_podcast_items(url)

def create_podcast_items(url):    
    """This function creates podcast items"""
    root = api.retrieve_podcasts(url)
    # builds up menu item
    main_menu = [ {'thumbnail': podcast_image(item), 
        'info': {'type':'Audio', 'title': item[0].text}, 
        'path': p.get_plugin_path(action='play_audio', url=item[4].attrib['url']), 
        'IsPlayable': True, } for item in root.iter('item')]
    # add items to media playlist
    p.add_items(main_menu)

def podcast_image(item):
    """This function return the image location if show images is set."""
    image = ''
    if (settings.getSetting('podcast_images')=='true'):
         image = item[8].attrib['href'] 
    p.log("pureradio.podcast_image "+ image)
    return image

def play_audio(params):
    """This function plays the audio source."""
    p.log("pureradio.play_audio "+repr(params))
    url = params.get("url")
    if url:
        return p.play_resolved_url(url)
    else:
        p.showWarning(get_located_string('Audio not located'))    

def get_located_string(string_name):
    """This function returns the localized string if it is available."""
    return translation(localized_strings.get(string_name)) or string_name if string_name in localized_strings else string_name
