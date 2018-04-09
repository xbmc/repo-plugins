# # -*- coding: utf-8 -*-
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import sys
import urllib
import urlparse
import requests
import youtube_resolver
from resources.lib.kodiutils import get_string

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

_addon = xbmcaddon.Addon()
_icon = _addon.getAddonInfo('icon')


def scrap_website():
    """
    Scrap the website of lemediatv.fr to get the video id of the currently played video.
    """
    url = "https://cms.inscreen.tv/Api/program/list/95/undefined"
    r = requests.get(url)
    playlist = r.json()
    videoid = playlist[0]['videoid']
    return videoid


def resolve_url(videoid):
    """
    Resolve the url in a playable stream using youtube_resolver from the youtube plugin
    """
    live = False
    try:
        streams = youtube_resolver.resolve(videoid)
    except Exception:
        dialog = xbmcgui.Dialog()
        dialog.notification(get_string(32002), get_string(32003), xbmcgui.NOTIFICATION_INFO, 10000)
        quit()
    if streams:
        if streams[0].get('Live'):
            if xbmc.getCondVisibility('System.HasAddon(%s)' % 'inputstream.adaptive') == 1:
                streams = [stream for stream in streams if (stream.get('container') == 'mpd' and stream.get('Live') is True)]
                live = True
            else:
                dialog = xbmcgui.Dialog()
                dialog.notification(get_string(32004), get_string(32005), xbmcgui.NOTIFICATION_INFO, 7500)
                return False
        if streams:
            stream = streams[0]
        title = get_string(32006) + stream.get('meta', {}).get('video', {}).get('title', '').encode('latin1')
        thumbnail = stream.get('meta', {}).get('images', {}).get('high', '')
        stream_url = stream.get('url', '')
        stream_headers = stream.get('headers', '')
        if stream_headers:
            stream_url += '|' + stream_headers
        play_item = xbmcgui.ListItem(label=title, path=stream_url)
        play_item.setInfo('video', {'Genre': 'Video', 'plot': get_string(32000)})
        play_item.setArt({'poster': thumbnail, 'thumb': thumbnail})
        play_item.setContentLookup(False)
        if live:
            play_item.setMimeType('application/xml+dash')
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            if stream_headers:
                play_item.setProperty('inputstream.adaptive.stream_headers', stream_headers)
        return play_item
    else:
        dialog = xbmcgui.Dialog()
        dialog.notification(get_string(32007), get_string(32005), xbmcgui.NOTIFICATION_INFO, 7500)
        return False


class MyPlayer(xbmc.Player):
    """
    Create a custom player to concatenate the videos
    """
    def onPlayBackEnded(self):
        xbmc.executebuiltin("XBMC.PlayMedia(plugin://plugin.video.lemediatv/?mode=play)")


def play_video():
    """
    Play the last video played in the website
    """
    videoid = scrap_website()
    play_item = resolve_url(videoid)
    if play_item:
        player = MyPlayer()
        player.play(play_item.getPath(), listitem=play_item)

        # Wait until playback starts
        xbmc.sleep(500)
        while player.isPlaying():
            xbmc.sleep(500)


xbmc.log("[plugin.video.lemedia]: Started Running")

# Following the url used to access the plugin
if sys.argv[2] == '':
    # Build the addon url (plugin://)
    url = base_url + '?' + urllib.urlencode({'mode': 'play'})

    li = xbmcgui.ListItem(get_string(32000))
    li.setProperty('IsFolder', 'False')
    li.setArt({'thumb': 'https://www.lemediatv.fr/sites/default/files/media-logo.png'})
    li.setContentLookup(False)
    li.addStreamInfo('audio', {'language': 'fr'})
    li.setInfo('video', {'Title': get_string(32001), 'Genre': 'Video', 'plot': get_string(32000)})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    xbmcplugin.endOfDirectory(addon_handle)

else:
    play_video()

xbmc.log("[plugin.video.lemedia]: Finished Running")
