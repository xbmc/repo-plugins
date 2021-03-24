# Module: main
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# -*- coding: utf-8 -*-

"""
Ruyjinx game addon
"""
import sys
from urllib.parse import urlencode, parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import json
import subprocess
import base64
import os
from PIL import Image
import io
import platform

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])

MONITOR_MODEL='XWAYLAND17'
def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(_URL, urlencode(kwargs))

import unicodedata
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
def list_games():
    """
    Create the list of playable games in the Kodi interface.

    :type category: str
    """
    emulator_path = xbmcaddon.Addon().getSettingString('emulator_path')
    game_dir_path = xbmcaddon.Addon().getSettingString('game_dir_path')
    result = subprocess.run([emulator_path, '--list-games', game_dir_path], stdout=subprocess.PIPE)
    #xbmc.log('------ {}'.format(result), xbmc.LOGINFO)
    arrayMetadataGame = json.loads(result.stdout)
     
     
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_HANDLE, 'games')
    # Iterate through games.
    for game in arrayMetadataGame:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=game['title_name'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        title_name = game['title_name']
        list_item.setInfo('game', {'title': title_name,
                                    'path': game['path'],
                                    'mediatype': 'game'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        img_data = game['icon']
        im = Image.open(io.BytesIO(base64.b64decode(img_data)))
        img_name = title_name + '.png'
        temp_folder = xbmcvfs.translatePath('special://temp')
        img_dir = os.path.join(temp_folder, 'Ryujinx')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        img_path = os.path.join(img_dir, img_name)
        xbmc.log('------ {}'.format(img_path), xbmc.LOGINFO)
        try:
           im.save(img_path)
        except:
            img_path = os.path.join(img_dir, strip_accents(img_name))
            xbmc.log('------ {}'.format(img_path), xbmc.LOGINFO)
            im.save(img_path)

        list_item.setArt({'thumb': img_path, 'icon': img_path, 'fanart': img_path})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        url = get_url(action='play', game=game['path'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_HANDLE)


def play_game(path):
    """
    Play a game by the provided path.

    :param path: Fully-qualified game path
    :type path: str
    """
    # Create a playable item with a path to play.
    #play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    #xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)

    env=os.environ.copy()
    #Ignore wayland
    if platform.system() == 'Linux':
        env['GDK_BACKEND'] = 'x11'
        #env['__GLX_VENDOR_LIBRARY_NAME'] = 'nvidia'
        #env['DRI_PRIME'] = '1'
    #TODO: Run in same screen as kodi (for multimonitor config
    #env['DISPLAY'] = ':0.1'
    
    emulator_path = xbmcaddon.Addon().getSettingString('emulator_path')
    command = [emulator_path, '--run-once', '-f', path, '--move', MONITOR_MODEL]
    xbmc.log('------ {}'.format(command), xbmc.LOGINFO)
    p = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #p.wait()
    stdout, stderr = p.communicate()
    xbmc.log('------ subprocess result {}'.format(stdout), xbmc.LOGINFO)
    xbmc.log('------ subprocess result {}'.format(stderr), xbmc.LOGINFO)
    #TODO: Listen to ESC or EXIT on kodi to kill process
    #p.terminate()


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """

    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params and 'action' in params:
        action = params['action']
        if action == 'play':
            # Play a game from a provided URL.
            play_game(params['game'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid action: {}!'.format(action))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of games
        list_games()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    xbmc.log('------ {}'.format(sys.argv), xbmc.LOGINFO)
    paramstring = sys.argv[2][1:]
    router(paramstring)
