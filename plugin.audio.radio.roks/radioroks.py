# coding=utf-8
# Kodi addon for radio Roks online streams
# developed by E.Kuzin

#  Copyright 2017 Eugene Kuzin
#
#  This file is part of the radio.roks Kodi plugin.
#
#  This plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this plugin.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import urllib
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xml.etree.ElementTree as ET
import random

VERSION = '0.1.1'


def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)


def play_song(url, icon):
    # set the path of the song to a list item
    play_item = xbmcgui.ListItem(path=url)
    play_item.setArt({'thumb': icon})
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


# build playlist
def parse_channels():
    play_list = []
    channels_path = os.path.join(addon_path, 'resources', 'data', 'channels.xml')
    tree = ET.parse(channels_path)
    channels = tree.getroot()
    for channel in channels.findall('channel'):
        # check minimum required channel data
        if channel.find('name_id').text is not None:
            # get localized channel names
            name_id = int(channel.find('name_id').text)
            name = addon.getLocalizedString(name_id).encode('utf-8')
            if low_bitrate:
                url = channel.find('url32').text
            else:
                url = channel.find('url').text
            # no url - no display
            if url == '':
                pass
            # icon, default if not configured
            if channel.find('icon') is not None:
                icon = channel.find('icon').text
            else:
                icon = None
            if icon is None:
                icon = 'DefaultMusicCompilations.png'
            else:
                icon = os.path.join(addon_path, 'resources', 'media', channel.find('icon').text)
            # now add ListItem
            li = xbmcgui.ListItem(label=name)
            li.setArt({'icon': icon,
                       'thumb': icon})
            # set random fanart
            fanarts = channel.findall('fanart')
            if len(fanarts) > 0:
                fanart_file = fanarts[random.randint(0, len(fanarts)-1)].text
                fanart_path = os.path.join(addon_path, 'resources', 'media', fanart_file)
            else:
                fanart_path = os.path.join(addon_path, 'fanart.jpg')
            li.setArt({'fanart': fanart_path})
            # set Info
            li.setInfo('music', {'genre': 'Rock', 'artist': name, 'title': 'Online Stream'})
            # set the list item to playable
            li.setProperty('IsPlayable', 'true')
            # build the plugin url for Kodi
            url = build_url({'mode': 'stream', 'url': url, 'title': name, 'icon': icon})
            # add the current list item to a list
            play_list.append((url, li, False))
        else:
            pass
    return play_list


# parse channels info from settings
def build_playlist():
    play_list = parse_channels()
    # add list to Kodi
    xbmcplugin.addDirectoryItems(addon_handle, play_list, len(play_list))
    # set the content of the directory
    xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)


# get call params
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

# get settings
addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path').decode('utf-8')
low_bitrate = (False, True)[addon.getSetting('low_bitrate') == 'true']
lang = xbmc.getLanguage(xbmc.ISO_639_1)

# initial run
if mode is None:
    # display the list of channels in Kodi
    build_playlist()
# a song from the list has been selected
elif mode[0] == 'stream':
    # pass the url of the song to play_song
    play_song(args['url'][0], args['icon'][0])

