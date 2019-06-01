# -*- coding: utf-8 -*-
"""
    IMDB Trailers Kodi Addon
    Copyright (C) 2018 gujal
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Imports
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
import re
import sys
import urllib.request, urllib.error, urllib.parse
import datetime
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import html.parser
from bs4 import BeautifulSoup, SoupStrainer

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer


# DEBUG
DEBUG = False

_addon = xbmcaddon.Addon()
_addonID = _addon.getAddonInfo('id')
_plugin = _addon.getAddonInfo('name')
_version = _addon.getAddonInfo('version')
_icon = _addon.getAddonInfo('icon')
_fanart = _addon.getAddonInfo('fanart')
_language = _addon.getLocalizedString
_settings = _addon.getSetting
PY3 = sys.version_info[0] == 3
force_mode = _settings("forceViewMode") == "true"
if force_mode:
    menu_mode = int(_settings('MenuMode'))
    view_mode = int(_settings('VideoMode'))
cache = StorageServer.StorageServer('imdbtrailers', _settings('timeout'))
CONTENT_URL = 'https://www.imdb.com/trailers/'
SHOWING_URL = 'https://www.imdb.com/movies-in-theaters/'
COMING_URL = 'https://www.imdb.com/movies-coming-soon/{}-{:02}'
DETAILS_PAGE = "https://m.imdb.com/videoplayer/{}"
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.17'

if not xbmcvfs.exists('special://profile/addon_data/'+_addonID+'/settings.xml'):
    _addon.openSettings()

class Main(object):
    def __init__(self):
        if ('action=list2' in sys.argv[2]):
            self.list_contents2()
        elif ('action=list' in sys.argv[2]):
            self.list_contents()
        elif ('action=play' in sys.argv[2]):
            self.play()
        elif ('action=clear' in sys.argv[2]):
            self.clear_cache()
        else:
            self.main_menu()


    def main_menu(self):
        if DEBUG:
            self.log('main_menu()')
        category = [{'title':_language(30201), 'key':'showing'},
                    {'title':_language(30202), 'key':'coming'},
                    {'title':_language(30203), 'key':'popTab'},
                    {'title':_language(30204), 'key':'recAddTab'},
                    {'title':_language(30205), 'key':'tvTab'},
                    {'title':_language(30206), 'key':'cache'}]
        for i in category:
            listitem = xbmcgui.ListItem(i['title'])
            listitem.setArt({'thumb': _icon,
                             'fanart': _fanart,
                             'icon' : _icon})

            if i['key'] == 'cache':
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'clear'})
            elif i['key'] == 'showing' or i['key'] == 'coming':
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'list2', 'key': i['key']})
            else:
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'list', 'key': i['key']})
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(url, listitem, True)])
    
        # Sort methods and content type...
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setContent(int(sys.argv[1]), 'addons')
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(menu_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)


    def clear_cache(self):
        """
        Clear the cache database.
        """
        msg = 'Cached Data has been cleared'
        cache.table_name = 'imdbtrailers'
        cache.cacheDelete('%fetch%')
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(_plugin, msg, 3000, _icon))
    
    
    def list_contents(self):
        if DEBUG:
            self.log('content_list()')
        videos,jdata = cache.cacheFunction(fetchdata,self.parameters('key'))
        h = html.parser.HTMLParser()
        for video in videos:
            videoId = video.get('data-videoid')
            jd = jdata[videoId]
          
            plot = html.unescape(jd['description']) if PY3 else h.unescape(jd['description'])
            director = jd['directorNames']
            cast = jd['starNames']
            title = jd['titleName']
            tname = jd['trailerName']
            imdb = jd['titleId']
            fanart = jd['slateUrl'].split('_')[0] + 'jpg'
            poster = jd['posterUrl'].split('_')[0] + 'jpg'
            icon = jd['posterUrl']
            try:
                duration = jd['trailerLength']
            except:
                duration = 0

            try:
                tyear = jd['titleNameWithYear']
                year = int(re.findall('\((\d{4})',tyear)[0])
            except:
                year = 1900

            listitem = xbmcgui.ListItem(title)
            listitem.setArt({'thumb': poster,
                             'icon' : icon,
                             'poster': poster,
                             'fanart': fanart})

            listitem.setInfo(type='video',
                             infoLabels={'title': title,
                                         'originaltitle': tname,
                                         'plot': plot,
                                         'year': year,
                                         'duration': duration,
                                         'imdbnumber': imdb,
                                         'director': director,
                                         'cast': cast})

            listitem.setProperty('IsPlayable', 'true')
            url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'play',
                                                        'videoid': videoId})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

        # Sort methods and content type...
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)


    def list_contents2(self):
        if DEBUG:
            self.log('content_list2()')
        if self.parameters('key') == 'showing':
            page_data = cache.cacheFunction(fetch,SHOWING_URL)
            tlink = SoupStrainer('div', {'id': 'main'})
        else:
            year, month, day = datetime.date.today().isoformat().split('-')
            page_data = b'' if PY3 else ''
            for i in range(4):
                url = COMING_URL.format(year, int(month)+i)
                page_data += cache.cacheFunction(fetch, url)
            tlink = SoupStrainer('div', {'class': 'list detail'})
        
        mdiv = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
        videos = mdiv.find_all('table')
        h = html.parser.HTMLParser()

        for video in videos:
            vdiv = video.find('a', {'itemprop': 'trailer'})
            if vdiv:
                videoId = vdiv.get('href').split('?')[0].split('/')[-1]
                plot = html.unescape(video.find(class_='outline').text).strip() if PY3 else h.unescape(video.find(class_='outline').text).strip()
                tdiv = video.find(class_='image')
                icon = tdiv.find('img')['src']
                title = tdiv.find('img')['title']
                imdb = tdiv.find('a')['href'].split('/')[-2]
                poster = icon.split('_')[0] + 'jpg'
                try:
                    year = int(re.findall(r'\((\d{4})',title)[0])
                    title = re.sub(r'\s\(\d{4}\)', '', title)
                except:
                    year = 1900
                infos = video.find_all(class_='txt-block')
                director = []
                directors = infos[0].find_all('a')
                for name in directors:
                    director.append(name.text)
                cast = []
                stars = infos[1].find_all('a')
                for name in stars:
                    cast.append(name.text)

                listitem = xbmcgui.ListItem(title)
                listitem.setArt({'thumb': poster,
                                 'icon' : icon,
                                 'poster': poster,
                                 'fanart': _fanart})

                listitem.setInfo(type='video',
                                 infoLabels={'title': title,
                                             'plot': plot,
                                             'year': year,
                                             'imdbnumber': imdb,
                                             'director': director,
                                             'cast': cast})

                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'play',
                                                            'videoid': videoId})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

        # Sort methods and content type...
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)


    def get_video_url(self):
        if DEBUG:
          self.log('get_video_url()')
        quality = _settings("video_quality")
        detailsUrl = DETAILS_PAGE.format(self.parameters('videoid'))
        if DEBUG:
          self.log('detailsURL: %s' % detailsUrl)
        details = str(fetch(detailsUrl))
        v = re.match(r'definition":"%s".+?Url":"([^"]+)'%quality, details)
        if v:
            videoUrl = v.group(1)
        else:
            videoUrl = re.findall(r'definition":"\d+p".+?Url":"([^"]+)', details)[0]
        if DEBUG:
          self.log('videoURL: %s' % videoUrl)
        videoUrl = videoUrl.replace('\\u002F','/').replace('\\/','/')
        if DEBUG:
          self.log('cleaned videoURL: %s' % videoUrl)
        return videoUrl


    def play(self):
        if DEBUG:
          self.log('play()')
        title = xbmc.getInfoLabel("ListItem.Title")
        thumbnail = xbmc.getInfoImage("ListItem.Thumb")
        plot = xbmc.getInfoLabel("ListItem.Plot")
        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({ 'thumb': thumbnail })

        # set the key information
        listitem.setInfo('video', {'title': title,
                                   'label': title,
                                   'plot': plot,
                                   'plotOutline': plot})

        listitem.setPath(self.get_video_url())
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listitem)


    def parameters(self, arg):
        _parameters = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)
        return _parameters[arg][0]


    def log(self, description):
        xbmc.log("[ADD-ON] '{} v{}': {}".format(_plugin, _version, description), xbmc.LOGNOTICE)


def fetch(url):

    headers = {'User-Agent': USER_AGENT}
    req = urllib.request.Request(url, None, headers)
    data = urllib.request.urlopen(req).read()
    return data


def fetchdata(key):

    page_data = cache.cacheFunction(fetch,CONTENT_URL)
    tlink = SoupStrainer('div', {'id':key})
    jlink = SoupStrainer('script', {'id':'imdbTrailerJson'})
    tabclass = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
    jdata = BeautifulSoup(page_data, "html.parser", parse_only=jlink)
    items = tabclass.findAll('div', {'class':re.compile('^gridlist-item')})
    jd = json.loads(jdata.text)    
    return items,jd

    
if __name__ == '__main__':
  Main()
