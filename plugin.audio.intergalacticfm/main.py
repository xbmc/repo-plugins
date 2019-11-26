# -*- coding: utf-8 -*-
# Module: default
# Author: Pander
# Created on: 2019-03-04
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from json import load
from sys import argv
from os.path import isfile
import requests

from urllib import urlencode
from urlparse import parse_qsl


import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmc import log, LOGDEBUG

__addonid__ = "plugin.audio.intergalacticfm"
base = xbmc.translatePath('special://home/addons/{}/resources/'.format(__addonid__))

# Get the plugin url in plugin:// notation.
_url = argv[0]
# Get the plugin handle as an integer number.
_handle = int(argv[1])

_addon = xbmcaddon.Addon()

def list_audios():
    """
    Create the list of playable streams in the Kodi interface.
    """

    radio = 'http://radio.intergalactic.fm:80/'
    streams = load(open(base + 'streams.json'))
    listing = []

    xbmcplugin.setPluginCategory(_handle, 'Live Streams')
    xbmcplugin.setContent(_handle, 'videos')

    for key, audio in streams.items():
        list_item = xbmcgui.ListItem(label=audio['label'])
        list_item.setInfo(type='video', infoLabels={'genre': audio['genre'], 'plot': audio['plot'], 'tagline': audio['tagline']})

        # see https://kodi.wiki/view/Movie_artwork
        # only poster, fanart and clearlogo is supported/needed

        art = {}

        #log(__addonid__ + ' key: ' + key, LOGDEBUG)
        # poster 1000x1500 1:1.5 PNG
        poster = '{}{}-poster.png'.format(base, key)
        if isfile(poster):
            art['poster'] = poster
        else: # note: specific fallback
            art['poster'] = '{}intergalactic_radio-poster.png'.format(base)
        #log(__addonid__ + ' poster: ' + art['poster'], LOGDEBUG)

        # fanart 1920x1080 16:9 JPG
        fanart = '{}{}-fanart.jpg'.format(base, key.split('_')[0])
        if isfile(fanart):
            art['fanart'] = fanart
        else: # note: specific fallback
            art['fanart'] = '{}fanart.jpg'.format(base)
        #log(__addonid__ + ' fanart: ' + art['fanart'], LOGDEBUG)

        # clearlogo 800x310 1:0.388 transparent PNG (is top-left corner overlay)
        art['clearlogo'] = '{}intergalactic_radio-clearlogo.png'.format(base)

        list_item.setArt(art)
        list_item.setProperty('IsPlayable', 'true')

        url = '{}{}'.format(radio, audio['file'])
        log(__addonid__ + ' url: ' + url, LOGDEBUG)
        url = '{}?action=play&video={}'.format(_url, url)
        log(__addonid__ + ' url: ' + url, LOGDEBUG)
        is_folder = False

        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


def play_audio(path):
    """
    Play audio by the provided path.
    :param path: Fully-qualified audio URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
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
    params = dict(parse_qsl(paramstring[1:]))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of audios in a provided category.
            list_audios()
        elif params['action'] == 'play':
            # Play audio from a provided URL.
            play_audio(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_audios()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    router(sys.argv[2])
