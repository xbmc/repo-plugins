#!/usr/bin/env python
# -*- coding: utf-8 -*-
########################################
# Nectarine Demoscene XBMC Plugin
########################################
#
# Copyright (c) 2014 Vidar Waagbø
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import os
import sys
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmcaddon
from xml.dom import minidom
from httpcomm import HTTPComm
from ConfigParser import SafeConfigParser

pluginConfig = SafeConfigParser()
pluginConfig.read(os.path.join(os.path.dirname(__file__), "config.ini"))

ARGS = urlparse.parse_qs(sys.argv[2][1:])
BASE_URL = sys.argv[0]
HANDLE = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id=pluginConfig.get('plugin', 'id'))


class Main:

    def __init__(self):
        xbmcplugin.setContent(HANDLE, 'audio')

        self.curl = HTTPComm()

        self.name = ARGS.get('foldername', None)
        self.mode = ARGS.get('mode', None)

    def run(self):

        if self.mode is None:

            # Create streams directory
            url = self.build_url({'mode': 'folder', 'foldername': 'streams'})
            li = xbmcgui.ListItem(ADDON.getLocalizedString(30100), iconImage='DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)

            # Create queue directory
            url = self.build_url({'mode': 'folder', 'foldername': 'queue'})
            li = xbmcgui.ListItem(ADDON.getLocalizedString(30101), iconImage='DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=True)
            xbmcplugin.endOfDirectory(HANDLE)

        elif self.mode[0] == 'folder' and self.name[0] == 'streams':

            streams = self.get_streams()
            for stream in streams:
                li = xbmcgui.ListItem(stream['name'], iconImage='DefaultAudio.png')
                li.setInfo(type="Music", infoLabels={"Size": stream['bitrate'] * 1024})
                li.setProperty("IsPlayable", "true")
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=stream['url'], listitem=li, isFolder=False)

            xbmcplugin.endOfDirectory(HANDLE)

        elif self.mode[0] == 'folder' and self.name[0] == 'queue':

            history = self.get_history()

            # Currently Playing
            self.add_heading(ADDON.getLocalizedString(30200))
            for item in history[0]:
                li = xbmcgui.ListItem(item["artist"] + " - " + item["song"])
                li.setProperty("IsPlayable", "false")
                xbmcplugin.addDirectoryItem(handle=HANDLE, url="nnn", listitem=li, isFolder=False)


            # Queue
            self.add_heading(ADDON.getLocalizedString(30201), True)
            for item in history[1]:
                li = xbmcgui.ListItem(item["artist"] + " - " + item["song"])
                li.setProperty("IsPlayable", "false")
                xbmcplugin.addDirectoryItem(handle=HANDLE, url="nnn", listitem=li, isFolder=False)


            # History
            self.add_heading(ADDON.getLocalizedString(30202), True)
            for item in history[2]:
                li = xbmcgui.ListItem(item["artist"] + " - " + item["song"])
                li.setProperty("IsPlayable", "false")
                xbmcplugin.addDirectoryItem(handle=HANDLE, url="nnn", listitem=li, isFolder=False)

            xbmcplugin.endOfDirectory(HANDLE)

        else:

            # Add items
            url = 'http://no.scenemusic.net:9000/necta.m3u'
            li = xbmcgui.ListItem(ADDON.getLocalizedString(30199), iconImage='DefaultAudio.png')


            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url, listitem=li, isFolder=False)
            xbmcplugin.endOfDirectory(HANDLE)


    def build_url(self, query):
        return BASE_URL + '?' + urllib.urlencode(query)

    def get_streams(self):
        streams = []
        xml = self.curl.request(pluginConfig.get('urls', 'stream_xml'), 'get')
        dom = minidom.parseString(xml)

        for node in dom.getElementsByTagName('stream'):
            id = node.attributes["id"].value
            name = node.getElementsByTagName('name')[0].firstChild.nodeValue
            url = node.getElementsByTagName('url')[0].firstChild.nodeValue
            bitrate = int(node.getElementsByTagName('bitrate')[0].firstChild.nodeValue)
            country = node.getElementsByTagName('country')[0].firstChild.nodeValue
            type = node.getElementsByTagName('type')[0].firstChild.nodeValue

            streams.append({"id": id, "name": name, "url": url, 'bitrate': bitrate, 'country': country, 'type': type})

        streams = sorted(streams, key=lambda d: (d['name'][:6].lower(), -d['bitrate'])) #itemgetter('bitrate')
        return streams

    def get_history(self):
        current = []
        queue = []
        history = []

        xml = self.curl.request(pluginConfig.get('urls', 'history_xml'), 'get')
        dom = minidom.parseString(xml)

        # Currently Playing

        currentsong = dom.getElementsByTagName('now')[0]
        artist = currentsong.getElementsByTagName('artist')[0].firstChild.nodeValue
        song = currentsong.getElementsByTagName('song')[0].firstChild.nodeValue
        current.append({"artist": artist, "song": song})

        # Read queue

        for entry in dom.getElementsByTagName('queue')[0].getElementsByTagName('entry'):
            artist = entry.getElementsByTagName('artist')[0].firstChild.nodeValue
            song = entry.getElementsByTagName('song')[0].firstChild.nodeValue
            play_start = entry.getElementsByTagName('playstart')[0].firstChild.nodeValue
            queue.append({"artist": artist, "song": song, "play_start": play_start})

        # Read history

        for entry in dom.getElementsByTagName('history')[0].getElementsByTagName('entry'):
            artist = entry.getElementsByTagName('artist')[0].firstChild.nodeValue
            song = entry.getElementsByTagName('song')[0].firstChild.nodeValue
            play_start = entry.getElementsByTagName('playstart')[0].firstChild.nodeValue
            history.append({"artist": artist, "song": song, "play_start": play_start})

        return [current, queue, history]

    def add_heading(self, title, linebreak=False):
        # Linebreak
        if linebreak:
            li = xbmcgui.ListItem()
            li.setProperty("IsPlayable", "false")
            xbmcplugin.addDirectoryItem(handle=HANDLE, url="nnn", listitem=li, isFolder=False)

        li = xbmcgui.ListItem(label="[COLOR FF007EFF]" + title + "[/COLOR]")
        li.setProperty("IsPlayable", "false")
        xbmcplugin.addDirectoryItem(handle=HANDLE, url="nnn", listitem=li, isFolder=False)


if __name__ == '__main__':
    Main().run()
