'''Kodi video plugin for Intergalactic FM'''

__author__ = 'Dreamer, Pander'
__copyright__ = 'GPL v.3 https://www.gnu.org/copyleft/gpl.html'

from json import load
from os.path import isfile
import sys
from urllib.parse import parse_qsl

import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmc import log, LOGDEBUG
from xbmcvfs import translatePath

__addonid__ = "plugin.audio.intergalacticfm"
base = translatePath(f'special://home/addons/{__addonid__}/resources/')
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()

def list_audios():
    """
    Create the list of playable streams in the Kodi interface.
    """
    streams = load(open(base + 'streams.json'))  # pylint:disable=consider-using-with,unspecified-encoding
    listing = []

    xbmcplugin.setPluginCategory(_handle, 'Live Streams')
    xbmcplugin.setContent(_handle, 'videos')

    for key, audio in streams.items():
        list_item = xbmcgui.ListItem(label=audio['label'])
        list_item.setInfo(type='video', infoLabels={'genre': audio['genre'],
                                                    'plot': audio['plot'],
                                                    'tagline': audio['tagline']})

        # see https://kodi.wiki/view/Movie_artwork
        # only poster, fanart and clearlogo is supported/needed
        art = {}
        #log(__addonid__ + ' key: ' + key, LOGDEBUG)
        # poster 1000x1500 1:1.5 PNG
        poster = f'{base}{key}-poster.png'
        if isfile(poster):
            art['poster'] = poster
        else: # note: specific fallback
            art['poster'] = f'{base}intergalactic_radio-poster.png'
        #log(__addonid__ + ' poster: ' + art['poster'], LOGDEBUG)

        # fanart 1920x1080 16:9 JPG
        fanart = f'{base}{key.split("_")[0]}-fanart.jpg'
        if isfile(fanart):
            art['fanart'] = fanart
        else: # note: specific fallback
            art['fanart'] = f'{base}fanart.jpg'
        #log(__addonid__ + ' fanart: ' + art['fanart'], LOGDEBUG)

        # clearlogo 800x310 1:0.388 transparent PNG (is top-left corner overlay)
        art['clearlogo'] = f'{base}intergalactic_radio-clearlogo.png'

        list_item.setArt(art)
        list_item.setProperty('IsPlayable', 'true')

        url = audio['url']
        log(__addonid__ + ' url: ' + url, LOGDEBUG)
        url = f'{_url}?action=play&video={url}'
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
            raise ValueError(f'Invalid paramstring: {paramstring}!')
    else:
        list_audios()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2])
