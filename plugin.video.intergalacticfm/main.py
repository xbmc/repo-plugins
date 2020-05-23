# -*- coding: utf-8 -*-
# Module: default
# Author: Dreamer, Pander
# Created on: 2018-10-07
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
from xbmc import log, LOGDEBUG, LOGERROR

__addonid__ = "plugin.video.intergalacticfm"
base = xbmc.translatePath('special://home/addons/{}/resources/'.format(__addonid__))

# Get the plugin url in plugin:// notation.
_url = argv[0]
# Get the plugin handle as an integer number.
_handle = int(argv[1])

_addon = xbmcaddon.Addon()


fm = 'https://www.intergalactic.fm/'
tv = 'https://www.intergalactic.tv/'
pn = 'ifm-system/playingnow.json'
pl = 'playlist.m3u8'


#TODO If JSON on ifm-site is younger, load that file. Otherwise, load local file.
streams = load(open(base + 'streams.json'))

def now_videos(streams):
    """
    Create list of available streams
    """

    r = requests.get('{}{}'.format(fm, pn))
    # log("{} JSON: {}".format(__addonid__, r.json()), LOGDEBUG)

    try:
        nowplay = r.json()
        npvids = nowplay['11']
        log(__addonid__ + ' npvids: {}'.format(npvids), LOGDEBUG)
    except Exception as e:
        npvids = []
        log(__addonid__ + ' Error with nowplay[\'11\'] {}'.format(e), LOGERROR)

    listvids = []

    for key in streams.keys(): # order is determined in streams.json
        if key in set(npvids):
            listvids.append(streams[key])
# Uncomment the next two lines to show offline streams for development only
#        else:
#            listvids.append(streams[key])

    return listvids


def list_videos():
    """
    Create the list of playable streams in the Kodi interface.
    """

    listing = []

    xbmcplugin.setPluginCategory(_handle, 'Channels')
    xbmcplugin.setContent(_handle, 'videos')

    videos = now_videos(streams)

    for video in videos:
        label = 'Live - {}'.format(video['label'])
        list_item = xbmcgui.ListItem(label=label)
        list_item.setInfo(type='video', infoLabels={'genre': video['genre'], 'plot': video['plot'], 'tagline': video['tagline']})

        # see https://kodi.wiki/view/Movie_artwork
        # only poster, fanart and clearlogo is supported/needed

        art = {}

        # poster 1000x1500 1:1.5 PNG
        poster = base + video['label'].lower().replace(' ', '_') + '-poster.png'
        if isfile(poster):
            art['poster'] = poster
        else: # note: specific fallback
            art['poster'] = base + 'intergalactic_tv-poster.png'
        #log(__addonid__ + ' poster: ' + art['poster'], LOGDEBUG)

        # fanart 1920x1080 16:9 JPG
        fanart = base + video['label'].lower().replace(' ', '_') + '-fanart.jpg'
        if isfile(fanart):
            art['fanart'] = fanart
        else: # note: specific fallback
            art['fanart'] = base + 'cbs_tv-fanart.jpg'
        #log(__addonid__ + ' fanart: ' + art['fanart'], LOGDEBUG)

        # clearlogo 800x310 1:0.388 transparent PNG (is top-left corner overlay)
        clearlogo = base + video['label'].lower().replace(' ', '_') + '-clearlogo.png'
        if isfile(clearlogo):
            art['clearlogo'] = clearlogo
        else: # note: specific fallback
            art['clearlogo'] = base + 'intergalactic_tv-clearlogo.png'
        #log(__addonid__ + ' clearlogo: ' + art['clearlogo'], LOGDEBUG)

        list_item.setArt(art)
        list_item.setProperty('IsPlayable', 'true')

        url = '{}{}{}'.format(tv, video['url'], pl)
        #log(__addonid__ + ' url: ' + url, LOGDEBUG)
        url = '{}?action=play&video={}'.format(_url, url)
        is_folder = False

        listing.append((url, list_item, is_folder))

#    list_item = xbmcgui.ListItem('YouTube IFM')
#    list_item.setProperty('IsPlayable', 'false')
#    list_item.setInfo(type='video', infoLabels={'genre': 'electro, acid, italo, disco', 'plot': 'The official YouTube channel of Intergalactic FM. Offers hundreds of videos, most are live sets recorded at the Panama Racing Club and IFM Fest in The Hague.', 'tagline': 'You Are Not Alone'})
#    art = {}
#    art['poster'] = base + 'intergalactic_youtube-poster.png'
#    art['fanart'] = base + 'cbs_tv-fanart.jpg'
#    art['clearlogo'] = base + 'intergalactic_tv-clearlogo.png'
#    list_item.setArt(art)
#    listing.append(('plugin://plugin.video.youtube/channel/UCyiBzmL0FAJlupsJJg5BNzQ/', list_item, True))
#
#    list_item = xbmcgui.ListItem('YouTube Viewlexx')
#    list_item.setProperty('IsPlayable', 'false')
#    list_item.setInfo(type='video', infoLabels={'genre': 'electro, acid', 'plot': 'The official YouTube channel of the record label Viewlexx, est. 1995. Also home to the sublabel Murder Capital and I-F\'s playlist The Daily Struggle.', 'tagline': 'V = for Viewlexx!'})
#    art = {}
#    art['poster'] = base + 'viewlexx_youtube-poster.png'
#    art['fanart'] = base + 'cbs_tv-fanart.jpg'
#    art['clearlogo'] = base + 'intergalactic_tv-clearlogo.png'
#    list_item.setArt(art)
#    listing.append(('plugin://plugin.video.youtube/channel/UCNNH5GlnJvmNSUS53qNa8jg/', list_item, True))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


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
            # Display the list of videos in a provided category.
            list_videos()
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_videos()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    router(sys.argv[2])
