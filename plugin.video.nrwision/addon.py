#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import urllib2
import urlparse
import codecs

import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from xbmcswift import Plugin, download_page, xbmc, xbmcgui
from xbmcswift.ext.playlist import playlist

# UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

pluginBaseUrl = sys.argv[0]
addonHandle = int(sys.argv[1])

PLUGIN_NAME = 'nrwision'
PLUGIN_ID = 'plugin.video.nrwision'
BASE_URL = 'http://wwwocf.nrwision.de'
ART_BASE_URL = BASE_URL + '/fileadmin/kodi/images'
BACKGROUND = ART_BASE_URL + '/kodi_hintergrund.png'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30 Kodi'
FILE_NOT_FOUND = ''

plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)
plugin.register_module(playlist, url_prefix='/_playlist')
addon = xbmcaddon.Addon(id=PLUGIN_ID)

xbmcplugin.setContent(addonHandle, 'tvshows')


# Hauptmenü
@plugin.route('/', default=True)
def show_homepage():
    xbmc.executebuiltin('Container.SetViewMode(500)')

    addMenuEntry('live', addon.getLocalizedString(30007), '/kodi_live.png', BACKGROUND)
    addMenuEntry('tipps', addon.getLocalizedString(30001), '/kodi_tippsderwoche.png', BACKGROUND)
    addMenuEntry('videocharts', addon.getLocalizedString(30002), '/kodi_videocharts.png', BACKGROUND)
    addMenuEntry('woche', addon.getLocalizedString(30006), '/kodi_aktuell.png', BACKGROUND)
    addMenuEntry('themen', addon.getLocalizedString(30003), '/kodi_themen.png', BACKGROUND)
    addMenuEntry('orte', addon.getLocalizedString(30004), '/kodi_orte.png', BACKGROUND)
    addMenuEntry('suche', addon.getLocalizedString(30005), '/kodi_suche.png', BACKGROUND)

    xbmcplugin.endOfDirectory(addonHandle)
    return []

# Tipps
@plugin.route('/tipps/')
def tipps():
    buildList('/programm/tipps-der-woche.html?type=5001')
    return []

# aktuelle Woche
@plugin.route('/woche/')
def woche():
    buildList('/programm/aktuell.html?type=5001')
    return []

# Chartsmenü
@plugin.route('/videocharts/', default=True)
def videocharts():
    buildMenuFromJson('/fileadmin/kodi/menus/charts.json')
    return []

# Themen Menü
@plugin.route('/themen/')
def themen():
    buildMenuFromJson('/fileadmin/kodi/menus/themen.json')
    return []

# Orte Menü
@plugin.route('/orte/')
def orte():
    buildMenuFromJson('/fileadmin/kodi/menus/orte_abisz.json')
    return []

@plugin.route('/orte2/<url>/')
def orte2(url):
    buildMenuFromJson(url)
    return []

@plugin.route('/live/')
def live():
    li = xbmcgui.ListItem('Live', iconImage='/kodi_live.png')
    xbmc.Player().play('rtmp://fms.nrwision.de/live playpath=livestream swfUrl=http://www.nrwision.de/typo3conf/ext/user_pxcontent/res/player5.swf pageUrl=https://www.nrwision.de/programm/livestream.html swfVfy=true live=true', li)
    return []

# Suche
@plugin.route('/suche/')
def suche():
    keyboard = xbmc.Keyboard('', addon.getLocalizedString(30005))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        buildListFromSearch('/programm/sendungen/suche.html?type=5000&no_cache=1&h=&fuzzy=1&q=' + search_string)

# Menü aus Suchergebnis
@plugin.route('/search/<url>/')
def search(url):
    buildListFromSearch(url)
    return []

# Menü aus Flow Element
@plugin.route('/flow/<url>/')
def flow(url):
    buildList(url)
    return []

# Video anzeigen
@plugin.route('/view/')
def view():
    args = urlparse.parse_qs(sys.argv[2][1:])
    url = args['url'][0]
    title = args['title'][0]
    icon = args['icon'][0]
    li = xbmcgui.ListItem(title, iconImage=icon)
    #xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    xbmc.Player().play(url, li)
    return []

# Menüeintrag hinzufügen
def addMenuEntry(destination, title, icon, background):
    url = plugin.url_for(destination)
    li = xbmcgui.ListItem(title, iconImage=ART_BASE_URL + icon)
    li.setProperty('fanart_image', background)
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    return []

def addSubmenuEntry(destination, arguments, title, icon, background):
    url = plugin.url_for(destination, url=arguments)
    li = xbmcgui.ListItem(title, iconImage=ART_BASE_URL + icon)
    li.setProperty('fanart_image', background)
    xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    return []

# Video-Menü zusammenstellen / Type 5001
def buildList(sourceUrl):
    data = requestUrl(sourceUrl)

    if data != []:
        xbmc.executebuiltin('Container.SetViewMode(515)')

        for show in data['result']:
            xbmc.log(show['title'])
            url = plugin.url_for('view', url=show.get('video5', FILE_NOT_FOUND), title=show['title'], icon=show['imgpath'])
            li = xbmcgui.ListItem(
                show['title'],
                iconImage=BASE_URL + '/' + show['imgpath'])
            li.setProperty('fanart_image', BASE_URL + '/' + show['imgpath'])
            li.setInfo(
                type="Video",
                infoLabels={
                    'title': show['title'],
                    'duration': float(show['dauer'])/60,
                    'plot': show['longDesc'],
                    'genre': show['category'].strip(),
                    'year': show['premiered'][:4],
                    'aired': show['premiered']
                }
            )
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
        xbmcplugin.endOfDirectory(addonHandle)
    return []

# Video-Menü aus Suche zusammenstellen / Type 5000
def buildListFromSearch(sourceUrl):
    xbmc.log(sourceUrl)
    data = requestUrl(sourceUrl)

    if data != [] and data['result'] != []:
        xbmc.executebuiltin('Container.SetViewMode(515)')

        minNo = min(data['result'], key=int)
        maxNo = max(data['result'], key=int)

        for key in range(int(minNo), int(maxNo)+1):
            show = data['result'][str(key)]
            url = plugin.url_for('view', url=show['video5'], title=show['title'], icon=show['imgpath'])
            li = xbmcgui.ListItem(
                show['title'],
                iconImage=BASE_URL + '/' + show['imgpath'])
            li.setProperty('fanart_image', BASE_URL + '/' + show['imgpath'])
            li.setInfo(
                type="Video", infoLabels={
                    'title': show['title'],
                    'duration': float(show['dauer'])/60,
                    'plot': show['longDesc'],
                    'genre': show['tv_kategorie'].strip(),
                    'year': show['premiered'][:4],
                    'aired': show['premiered']
                }
            )
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)

        maxElements = int(data['params']['count'])
        if maxElements > int(maxNo):
            addSubmenuEntry('search', codecs.encode(sourceUrl + '&s=' + str(int(maxNo) + 1),'utf-8'), addon.getLocalizedString(30100), '/kodi_weiter.png', BACKGROUND)
        xbmcplugin.endOfDirectory(addonHandle)
    else:
        dialog = xbmcgui.Dialog()
        dialog.ok(addon.getLocalizedString(30005), addon.getLocalizedString(30112))
    return []


# JSON-Menü zusammenstellen
def buildMenuFromJson(sourceUrl):
    data = requestUrl(sourceUrl)

    if data != []:
        xbmc.executebuiltin('Container.SetViewMode(' + data['params']['viewmode'] +')')

        for i in data['menu']:
            if ('stringId' in i):
                i['title'] = addon.getLocalizedString(i['stringId'])
            addSubmenuEntry(i['type'], i['url'] , i['title'], i['image'], BACKGROUND)
        xbmcplugin.endOfDirectory(addonHandle)
    return []


def requestUrl(sourceUrl):
    try:
        req = urllib2.Request(BASE_URL + sourceUrl, headers={'User-Agent' : USER_AGENT})
        data = json.load(urllib2.urlopen(req))
    except:
        data = []
        dialog = xbmcgui.Dialog()
        dialog.ok(addon.getLocalizedString(30110), addon.getLocalizedString(30111))
    return data

if __name__ == '__main__':
    plugin.run()