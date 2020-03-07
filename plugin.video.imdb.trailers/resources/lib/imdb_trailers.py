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
from builtins import object
import re
import sys
import datetime
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from bs4 import BeautifulSoup, SoupStrainer
import requests
import requests_cache
import urllib.parse
import html.parser

PY3 = sys.version_info[0] == 3

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
_addonpath = 'special://profile/addon_data/{}/'.format(_addonID)

force_mode = _settings("forceViewMode") == "true"
if force_mode:
    menu_mode = int(_settings('MenuMode'))
    view_mode = int(_settings('VideoMode'))

if not xbmcvfs.exists(_addonpath):
    xbmcvfs.mkdir(_addonpath)

CACHE_FILE = xbmc.translatePath(_addonpath + 'requests_cache')
requests_cache.install_cache(CACHE_FILE, backend='sqlite', expire_after=int(_settings('timeout')) * 3600)

CONTENT_URL = 'https://www.imdb.com/trailers/'
SHOWING_URL = 'https://www.imdb.com/movies-in-theaters/'
COMING_URL = 'https://www.imdb.com/movies-coming-soon/{}-{:02}'
ID_URL = 'https://www.imdb.com/_json/video/{}'
DETAILS_PAGE = "https://m.imdb.com/videoplayer/{}"
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.57 Safari/537.17'
quality = int(_settings("video_quality")[:-1])

if not xbmcvfs.exists(_addonpath + 'settings.xml'):
    _addon.openSettings()


class Main(object):
    def __init__(self):
        if ('action=list2' in sys.argv[2]):
            self.list_contents2()
        elif ('action=list' in sys.argv[2]):
            self.list_contents()
        elif ('action=play_id' in sys.argv[2]):
            self.play_id()
        elif ('action=play' in sys.argv[2]):
            self.play()
        elif ('action=search' in sys.argv[2]):
            self.search()
        elif ('action=clear' in sys.argv[2]):
            self.clear_cache()
        else:
            self.main_menu()

    def main_menu(self):
        if DEBUG:
            self.log('main_menu()')
        category = [{'title': _language(30201), 'key': 'showing'},
                    {'title': _language(30202), 'key': 'coming'},
                    {'title': _language(30203), 'key': 'popTab'},
                    {'title': _language(30204), 'key': 'recAddTab'},
                    {'title': _language(30205), 'key': 'tvTab'},
                    {'title': _language(30206), 'key': 'search'},
                    {'title': _language(30207), 'key': 'cache'}]
        for i in category:
            listitem = xbmcgui.ListItem(i['title'])
            listitem.setArt({'thumb': _icon,
                             'fanart': _fanart,
                             'icon': _icon})

            if i['key'] == 'cache':
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'clear'})
            elif i['key'] == 'search':
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'search'})
            elif i['key'] == 'showing' or i['key'] == 'coming':
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'list2',
                                                                  'key': i['key']})
            else:
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'list',
                                                                  'key': i['key']})
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
        requests_cache.get_cache().clear()
        xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)

    def search(self):
        keyboard = xbmc.Keyboard()
        keyboard.setHeading('Search IMDb by Title')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_text = urllib.parse.quote(keyboard.getText())
        else:
            search_text = ''
        if len(search_text) > 2:
            url = 'https://www.imdb.com/find?q={}&s=tt'.format(search_text)
            page_data = fetch(url)
            tlink = SoupStrainer('table', {'class': 'findList'})
            soup = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
            items = soup.find_all('tr')
            for item in items:
                imdb_id = item.find('a').get('href').split('/')[2]
                title = item.text.strip()
                icon = item.find('img')['src']
                poster = icon.split('_')[0] + 'jpg'
                listitem = xbmcgui.ListItem(title)
                listitem.setArt({'thumb': poster,
                                 'icon': icon,
                                 'poster': poster,
                                 'fanart': _fanart})

                listitem.setInfo(type='video',
                                 infoLabels={'title': title,
                                             'imdbnumber': imdb_id})

                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'play_id',
                                                                  'imdb': imdb_id})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

            # Sort methods and content type...
            xbmcplugin.setContent(int(sys.argv[1]), 'movies')
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
            if force_mode:
                xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
            # End of directory...
            xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)
        else:
            msg = 'Need atleast 3 characters'
            xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)
            return

    def list_contents(self):
        if DEBUG:
            self.log('content_list()')
        videos, jdata = fetchdata(self.parameters('key'))
        h = html.parser.HTMLParser() if not PY3 else None
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
                year = int(re.findall(r'\((\d{4})', tyear)[0])
            except:
                year = 1900

            listitem = xbmcgui.ListItem(title)
            listitem.setArt({'thumb': poster,
                             'icon': icon,
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
            page_data = fetch(SHOWING_URL)
            tlink = SoupStrainer('div', {'id': 'main'})
        else:
            year, month, day = datetime.date.today().isoformat().split('-')
            page_data = ''
            nyear = int(year)
            for i in range(4):
                nmonth = int(month) + i
                if nmonth > 12:
                    nmonth = nmonth - 12
                    nyear = int(year) + 1
                url = COMING_URL.format(nyear, nmonth)
                page_data += fetch(url)
            tlink = SoupStrainer('div', {'class': 'list detail'})

        mdiv = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
        videos = mdiv.find_all('table')
        h = html.parser.HTMLParser() if not PY3 else None

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
                    year = int(re.findall(r'\((\d{4})', title)[0])
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
                                 'icon': icon,
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

    def get_video_url(self, video_id):
        if DEBUG:
            self.log('get_video_url()')
        detailsUrl = DETAILS_PAGE.format(video_id)
        if DEBUG:
            self.log('detailsURL: %s' % detailsUrl)
        details = fetch(detailsUrl)
        if '"playbackDataKey"' in details:
            vid = re.findall(r'args\s*=\s*.+?playbackDataKey":\[?"([^"]+)', details)[0]
            vidurl = 'https://m.imdb.com/ve/data/VIDEO_PLAYBACK_DATA?key={}'.format(vid)
            details = fetch(vidurl)
        if quality == 480:
            vids = re.findall(r'definition":"(\d+)p".+?url":"([^"]+)', details, re.IGNORECASE)
            vids.sort(key=lambda x: int(x[0]), reverse=True)
            if DEBUG:
                self.log('Found %s videos' % len(vids))
            for qual, vid in vids:
                if int(qual) <= quality:
                    if DEBUG:
                        self.log('videoURL: %s' % vid)
                    videoUrl = vid.replace('\\u002F', '/').replace('\\/', '/')
                    if DEBUG:
                        self.log('cleaned videoURL: %s' % videoUrl)
                    return videoUrl
        else:
            vid = re.findall(r'definition":"auto".+?url":"([^"]+)', details, re.IGNORECASE)[0]
            hls = fetch(vid)
            hlspath = re.findall(r'(http.+/)', vid)[0]
            quals = re.findall(r'BANDWIDTH=([^,]+)[^x]+x(\d+).+\n([^\n]+)', hls)
            if DEBUG:
                self.log('Found %s qualities' % len(quals))
            quals = sorted(quals, key=lambda x: int(x[0]), reverse=True)
            if DEBUG:
                self.log('Found %s qualities after sort' % len(quals))
            for bw, qual, svid in quals:
                if int(qual) <= quality:
                    videoUrl = hlspath + svid
                    if DEBUG:
                        self.log('videoURL: %s' % videoUrl)
                    return videoUrl

    def play(self):
        if DEBUG:
            self.log('play()')
        title = xbmc.getInfoLabel("ListItem.Title")
        thumbnail = xbmc.getInfoImage("ListItem.Thumb")
        plot = xbmc.getInfoLabel("ListItem.Plot")
        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({'thumb': thumbnail})

        # set the key information
        listitem.setInfo('video', {'title': title,
                                   'plot': plot,
                                   'plotOutline': plot})

        listitem.setPath(self.get_video_url(self.parameters('videoid')))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listitem)

    def play_id(self):
        if DEBUG:
            self.log('play_id()')
        iurl = ID_URL.format(self.parameters('imdb'))
        if DEBUG:
            self.log('IMDBURL: %s' % iurl)
        details = json.loads(fetch(iurl))
        video_list = details['playlists'][self.parameters('imdb')]['listItems']
        if len(video_list) > 0:
            videoid = video_list[0]['videoId']
            if DEBUG:
                self.log('VideoID: %s' % videoid)
            title = xbmc.getInfoLabel("ListItem.Title")
            thumbnail = xbmc.getInfoImage("ListItem.Thumb")
            listitem = xbmcgui.ListItem(title)
            listitem.setArt({'thumb': thumbnail})
            # set the key information
            listitem.setInfo('video', {'title': title})

            encodings = details['videoMetadata'][videoid]['encodings']
            vids = []
            for item in encodings:
                if item['mimeType'] == 'video/mp4':
                    qual = "360p" if item["definition"] == "SD" else item["definition"]
                    vids.append((qual[:-1], item["videoUrl"]))
            vids.sort(key=lambda elem: int(elem[0]), reverse=True)
            for qual, vid in vids:
                if int(qual) <= quality:
                    if DEBUG:
                        self.log('videoURL: %s' % vid)
                    videoUrl = vid
                    break

            listitem.setPath(videoUrl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listitem)
        else:
            msg = 'No Trailers available'
            xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)

    def parameters(self, arg):
        _parameters = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)
        return _parameters[arg][0]

    def log(self, description):
        xbmc.log("[ADD-ON] '{} v{}': {}".format(_plugin, _version, description), xbmc.LOGNOTICE)


def fetch(url):
    headers = {'User-Agent': USER_AGENT}
    data = requests.get(url, headers=headers).text
    return data


def fetchdata(key):
    page_data = fetch(CONTENT_URL)
    tlink = SoupStrainer('div', {'id': key})
    jlink = SoupStrainer('script', {'id': 'imdbTrailerJson'})
    tabclass = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
    jdata = BeautifulSoup(page_data, "html.parser", parse_only=jlink)
    items = tabclass.findAll('div', {'class': re.compile('^gridlist-item')})
    jd = json.loads(jdata.text)
    return items, jd
