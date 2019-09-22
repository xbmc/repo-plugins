#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Copyright 2019 Amir Ammari
#
#  This file is part of the Radio Javan kodi plugin.
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

from os.path import join
from sys import argv
import urllib2
import json
from time import gmtime, strftime, strptime
from urllib import quote_plus, urlopen
from urlparse import parse_qs, urlparse
from xml.dom.minidom import parseString
from xbmc import translatePath
import xbmcaddon
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

ADDON = xbmcaddon.Addon()
ADDONNAME = ADDON.getAddonInfo('name')
ADDONID = ADDON.getAddonInfo('id')
ADDONVERSION = ADDON.getAddonInfo('version')
CWD = ADDON.getAddonInfo('path').decode("utf-8")
LANGUAGE = ADDON.getLocalizedString

DataLink = 'http://navahang.me/webservice/GetMp3?type=Featured&from=0&to=20'

class LoadLister:

        def __init__(self, url):
                self.url = url

        def addLink(self, name, url, image = '', info = {}, totalItems = 0):
                item = ListItem(name.encode('utf-8'), iconImage = image, thumbnailImage = image)
                item.setProperty('mimetype', 'audio/mpeg')
                item.setInfo('music', info)
                return addDirectoryItem(int(argv[1]), url, item, False, totalItems)

        def buildIndex(self):
                request = urllib2.Request(self.url, headers={'User-Agent' : 'Kodi'})
                response = urllib2.urlopen(request)
                json_text = response.read()
                loaded_json = json.loads(json_text)
                for item in loaded_json:
                        self.addLink(item['artist_name'] + ' - ' + item['song_name'], item['download'], item['image'], {'Artist': item['artist_name'],'Title': item['song_name'],'Album': 'Single'})

        def run(self, handle):
                endOfDirectory(int(handle))

if __name__ == '__main__':
        try:
                appClass = LoadLister(DataLink)
                appClass.buildIndex()
                appClass.run(argv[1])
                
        except urllib2.HTTPError as err:
                xbmcgui.Dialog().ok(ADDONNAME, LANGUAGE(30001) % err.code, LANGUAGE(30000))

        except:
                xbmcgui.Dialog().ok(ADDONNAME, LANGUAGE(30002), LANGUAGE(30000))
