import sys
import urllib
import urllib2
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
import re

from resources.lib import CBCJsonParser

# TODO Add logging info
# getting addon object
my_addon = xbmcaddon.Addon('plugin.audio.cbcradio')
# Localization info
language = my_addon.getLocalizedString

# base url and handle of the addon
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

# On first time launch, users can select their region, we use a String comparison (not boolean) since that is what getSetting returns
if my_addon.getSetting('3') == 'true':
    my_addon.openSettings()
    my_addon.setSetting('3', 'false')

# Get region setting for Radio 1
my_r1_region = my_addon.getSetting('0')

# Get region setting for Radio 2
my_r2_region = my_addon.getSetting('1')

# Get Quality setting
my_quality = my_addon.getSetting('2').decode('utf-8')

# 30004 is high quality
if my_quality == language(30004):
    qual = 0
else:
    qual = 1

xbmcplugin.setContent(addon_handle, 'songs')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode',None)

# Top-level menu
# FIXME, prettify this ugly copy/paste section
if mode is None:

    url = CBCJsonParser.parse_pls(CBCJsonParser.get_R1_streams(my_r1_region)[qual])
    li = xbmcgui.ListItem('Radio 1 (' + my_r1_region + ')', iconImage='DefaultAudio.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    url = CBCJsonParser.parse_pls(CBCJsonParser.get_R2_streams(my_r2_region))
    li = xbmcgui.ListItem('Radio 2 (' + my_r2_region + ')', iconImage='DefaultAudio.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    url = CBCJsonParser.parse_pls('http://playerservices.streamtheworld.com/pls/CBC_R3_WEB.pls')
    li = xbmcgui.ListItem('Radio 3', iconImage='DefaultAudio.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    url = CBCJsonParser.parse_pls('http://playerservices.streamtheworld.com/pls/CBC_SONICA_H.pls')
    li = xbmcgui.ListItem('Sonica', iconImage='DefaultAudio.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    url = build_url({'mode': 'Radio1', 'foldername': 'Folder One'})
    li = xbmcgui.ListItem(language(30006), iconImage='DefaultFolder.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'Radio2', 'foldername': 'Folder Two'})
    li = xbmcgui.ListItem(language(30007), iconImage='DefaultFolder.png')
    li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

# Populates directory with region links for Radio 1
elif mode[0] == 'Radio1':
    foldername = args['foldername'][0]
    regions = CBCJsonParser.get_regions('radio1')
    for region in regions:
        url = build_url({'mode': 'r1_regions', 'foldername': region})
        li = xbmcgui.ListItem(region, iconImage='DefaultFolder.png')
        li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

# Populates directory with region links for Radio 2
elif mode[0] == 'Radio2':
    foldername = args['foldername'][0]
    regions = CBCJsonParser.get_regions('radio2')
    for region in regions:
        playlist_url = CBCJsonParser.get_R2_streams(region)
        url = CBCJsonParser.parse_pls(playlist_url)
        li = xbmcgui.ListItem(region, iconImage='DefaultAudio.png')
        li.setProperty('fanart_image',my_addon.getAddonInfo('fanart'))
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)

# Create list items and URLs for Radio 1
elif mode[0] == 'r1_regions':
    region = args['foldername'][0].decode('utf-8')

    aac_playlist_url, mp3_playlist_url = CBCJsonParser.get_R1_streams(region)
    aac_stream_url = CBCJsonParser.parse_pls(aac_playlist_url)
    mp3_stream_url = CBCJsonParser.parse_pls(mp3_playlist_url)

    aac_li = xbmcgui.ListItem(region + ' - ' + language(30004), iconImage='DefaultAudio.png')
    mp3_li = xbmcgui.ListItem(region + ' - ' + language(30005), iconImage='DefaultAudio.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=aac_stream_url, listitem=aac_li)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=mp3_stream_url, listitem=mp3_li)
    xbmcplugin.endOfDirectory(addon_handle)
