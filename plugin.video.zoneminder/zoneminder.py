# -*- coding: utf-8 -*-
# Module: zoneminder
# Author: Peter Gallagher
# Created on: 2019-01-12
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
# Python3 equivalent
# from urllib.parse import quote, parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json

# Global vars
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_language = _addon.getLocalizedString
_base_url = _addon.getSetting('base_url').strip()
_zm_path = _addon.getSetting('zm_path').strip()
_cgi_path = _addon.getSetting('cgi_path').strip()
_auth_token = None
_auth_cookies = None

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    # Python3 equivalent
    # return '{0}?{1}'.format(_url, quote(kwargs))
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def error_message(message, title='Error'):
    sys.stderr.write(message)
    xbmcgui.Dialog().ok(title, message)

def login ():
    login_url = '{base_url}/{zm_path}/api/host/login.json'.format(base_url=_base_url, zm_path=_zm_path)
    creds = {
                'user': _addon.getSetting('username').strip(),
                'pass': _addon.getSetting('password').strip(),
                'stateful': 1
            }
    try:
        r = requests.post(login_url, data=creds)
    except requests.exceptions.RequestException as e:
        error_message(title=_language(33000), message=str(e))

    if r.status_code != 200:
        # Login failed
        error_message(title=_language(33001), message='{}: {}'.format(r.status_code, r.reason))

    j = json.loads(r.text)

    auth_token = j['credentials']
    auth_cookies = r.cookies
    return auth_token, auth_cookies

def get_active_monitors ():
    # Get monitors from Zoneminder API
    monitors_url = '{base_url}/{zm_path}/api/monitors.json'.format(base_url=_base_url, zm_path=_zm_path)
    r = requests.get(monitors_url, cookies=_auth_cookies)
    # Parse JSON response
    j = json.loads(r.text)

    active_monitors = []
    for monitor in j['monitors']:
        monitor = monitor['Monitor']

        if monitor['Enabled'] != '1':
            # If monitor is disabled in Zoneminder we don't want to display it so move to next item in array.
            continue

        active_monitor = dict()
        active_monitor['id'] = monitor['Id']
        active_monitor['name'] = monitor['Name']
        active_monitor['video'] = '{base_url}/{cgi_path}/nph-zms?scale=auto&width={width}&height={height}&mode=jpeg&maxfps={fps}&monitor={monitor_id}&{auth}'.format( 
            base_url=_base_url,
            cgi_path=_cgi_path,
            width=monitor['Width'],
            height=monitor['Height'],
            fps=_addon.getSetting('fps'),
            monitor_id=monitor['Id'],
            auth=_auth_token
            )
        
        active_monitor['thumb'] = '{base_url}/{cgi_path}/nph-zms?scale=auto&width={width}&height={height}&mode=single&maxfps={fps}&monitor={monitor_id}&{auth}'.format( 
            base_url=_addon.getSetting('base_url'),
            cgi_path=_cgi_path,
            width=monitor['Width'],
            height=monitor['Height'],
            fps=_addon.getSetting('fps'),
            monitor_id=monitor['Id'],
            auth=_auth_token
            )
        
        active_monitors.append(active_monitor)
    
    return active_monitors

def list_monitors():
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, _language(32001))
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    videos = get_active_monitors()
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video['name'],
                                    'mediatype': 'video'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', video=video['video'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Log into Zoneminder
    global _auth_token, _auth_cookies
    _auth_token, _auth_cookies = login()

    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))

    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['category'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_monitors()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])