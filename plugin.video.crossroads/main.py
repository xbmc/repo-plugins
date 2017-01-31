# -*- coding: utf-8 -*-
# Module: default
# Author: Doug Shannon, Chris Andrews, and Joe Kerstanoff based off sample plugin by Roman V. M.
# Created on: 26.1.2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
import os
import urlresolver
import requests
import re
import ast

# imports caching to SQLite cache database for function calls
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer
cache = StorageServer.StorageServer("crossroads", 1)

# Streamspot
_streamspot_url = 'https://api.streamspot.com/'
_streamspot_api_key = '82437b4d-4e38-42e2-83b6-148fcfaf36fb'
_streamspot_ssid = 'crossr4915'
_streamspot_header = {
    "Content-Type": 'application/json',
    "x-API-Key": _streamspot_api_key
}
_streamspot_player = '2887fba1'
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

def remove_non_ascii(text):
    """
    Removes non Ascii characters from a string
    """
    return ''.join([i if ord(i) < 128 else '' for i in text])

def cleanhtml(raw_html):
    """
    Turns HTML contents into just their strings
    """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_categories():
    """
    Get the list of video series.
    .. note:: Consider using `generator functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :return: The list of video categories
    :rtype: list
    """

    resp = requests.get('https://www.crossroads.net/proxy/content/api/series')
    data = resp.json()['series']
    data = filter(filter_series_with_no_videos, data)
    return data

def get_broadcaster():
    resp = requests.get('{}broadcaster/{}?players=true'.format(_streamspot_url, _streamspot_ssid), headers=_streamspot_header)
    return resp.json()['data']['broadcaster']

def get_broadcaster_stream_link(broadcaster):
    return broadcaster['live_src']['hls']

def filter_series_with_no_videos(series):
    """
    Filter out series that do not have any playable media
    """
    for event in series['messages']:
        if 'messageVideo' in event and event['messageVideo']['serviceId'] is not None:
            return True
    else:
        return False

def show_main_menu():
    """
    Create the initial interface for past or live series.
    """
    broadcaster = get_broadcaster()
    liveicon = os.path.join(os.path.dirname(__file__), 'resources', 'media', 'streaming.png')
    pastseries = os.path.join(os.path.dirname(__file__), 'resources', 'media', 'pastseries.png')
    fanart = os.path.join(os.path.dirname(__file__), 'fanart.jpg')

    if broadcaster['isBroadcasting']:
        # Live
        list_item_live = xbmcgui.ListItem(label='Watch live stream now')
        list_item_live.setInfo('video', {'title': 'Watch live stream now', 'plot': """Live Streams:
SAT 4:30 & 6:15pm 
SUN 8:30, 10:05 & 11:55am (EST)"""})
        list_item_live.setArt({'thumb': liveicon,
                               'icon': liveicon,
                               'fanart': fanart})
        url_live = get_url(action='play', video=get_broadcaster_stream_link(broadcaster))
        xbmcplugin.addDirectoryItem(_handle, url_live, list_item_live, False)

    # Historical
    list_item_past = xbmcgui.ListItem(label='Past Series')
    list_item_past.setInfo('video', {'title': 'Past Series', 'plot': 'Watch our previous weekend messages'})
    list_item_past.setArt({'thumb': pastseries,
                           'icon': pastseries,
                           'fanart': fanart})

    url_past = get_url(action='historical')
    xbmcplugin.addDirectoryItem(_handle, url_past, list_item_past, True)
    xbmcplugin.endOfDirectory(_handle)


def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Get video categories
    categories = cache.cacheFunction(get_categories)
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category['startDate'][5:] + ' ' + category['title'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        list_item.setArt({'thumb': category['image']['filename'],
                          'icon': category['image']['filename'],
                          'fanart': category['image']['filename']})
        # Set additional info for the list item.
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo

        list_item.setInfo('video',
                          {'title': category['title'],
                           'trailer': category['trailerLink'],
                           'plot': cleanhtml(category['description']),
                           'dateadded': category['startDate'],
                           'year': category['startDate'][:4]})
        # Create a URL for a plugin recursive call.
        # Example:
        # plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', series=category)
        # is_folder = True means that this item opens a sub-list of lower level
        is_folder = True
        # Add context Menu Option for trailer if it exists
        if category['trailerLink'] != None:
            traileurl = urlresolver.resolve(category['trailerLink'])
            list_item.addContextMenuItems([('Play Trailer', 'PlayMedia(' + traileurl + ')')])
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore
    # articles)
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def list_videos(series):
    """
    Create the list of playable videos in the Kodi interface.
    :param messages: Array of messages
    :type messages: json
    """
    series = ast.literal_eval(cleanhtml(series).replace('u\'', '\''))

    # Iterate through videos.
    for message in series['messages']:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=message['title'])
        # Set additional info for the list item.
        list_item.setInfo('video',
                          {'title': message['date'][5:] + ' ' + message['title'],
                           'genre': 'message', 'plot': message['description'],
                           'premiered': message.get('date', ""),
                           'dateadded': message.get('date', "")})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        if 'messageVideo' in message and 'still' in message['messageVideo']:
            imagesrc = message['messageVideo']['still']['filename']
        else:
            imagesrc = series['image']['filename']

        list_item.setArt({'thumb': imagesrc,
                          'icon': imagesrc,
                          'fanart': series['image']['filename']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example:
        # plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/vids/crab.mp4
        if 'messageVideo' in message and 'serviceId' in message['messageVideo']:
            vidurl = message['messageVideo']['serviceId']
        else:
            vidurl = ""

        url = get_url(action='play',
                      video="{}{}".format("https://www.youtube.com/watch?v=",
                                          vidurl))
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore
    # articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """

    if path[-4:] == 'm3u8':
        xbmc.Player().play(path)
    else:
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=urlresolver.resolve(path))
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


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
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided series.
            list_videos(params['series'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        elif params['action'] == 'historical':
            list_categories()
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        show_main_menu()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call
    # paramstring
    router(sys.argv[2][1:])
