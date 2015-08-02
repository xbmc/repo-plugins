#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    Gronkh.DE Kodi plugin
    Copyright (C) 2015  1750 Studios/Andreas Mieke

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, urlparse, urllib, json, datetime, os, hashlib, sqlite3, time, uuid, platform

import xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

from bs4 import BeautifulSoup
import requests

addonname       = 'plugin.video.gronkh.de'
addon           = xbmcaddon.Addon(id=addonname)
loc             = addon.getLocalizedString
cachedir        = 'special://userdata/addon_data/plugin.video.gronkh.de/caches/'

if sys.argv[1] == 'clearcache':
    dirs, files = xbmcvfs.listdir(cachedir)
    for f in files:
        xbmcvfs.delete(cachedir + f)
    dialog = xbmcgui.Dialog()
    dialog.notification('Gronkh.DE', loc(30004), xbmcgui.NOTIFICATION_INFO, 5000)
    quit()

addon_handle    = int(sys.argv[1])
addondir        = xbmc.translatePath(addon.getAddonInfo('profile'))

icondir         = 'special://home/addons/plugin.video.gronkh.de/resources/media/'
fanart          = 'special://home/addons/plugin.video.gronkh.de/fanart.jpg'

setting         = addon.getSetting
params          = urlparse.parse_qs(sys.argv[2][1:])

API_VERSION     = 2
API_URL         = 'http://gronkh.1750studios.com/api/'

baseurl         = API_URL + 'v' + str(API_VERSION) + '/'

twitchStreamInfo= 'https://api.twitch.tv/kraken/streams/'

twitchnames     = ['gronkh']

if not setting('user-id'):
    addon.setSetting('user-id', uuid.uuid4().hex[:16])

##### Helpers
def makeUrl(params):
    return sys.argv[0] + '?' + urllib.urlencode(params)

def getUserAgent():
    if setting('os'):
        return 'Kodi/' + xbmc.getInfoLabel('System.BuildVersionShort') + setting('os') + addon.getAddonInfo('version')
    kodiversion = xbmc.getInfoLabel('System.BuildVersionShort')
    addonversion = addon.getAddonInfo('version')
    busytext = xbmc.getLocalizedString(503)
    os = xbmc.getInfoLabel('System.OsVersionInfo')
    # This has to be done, since Kodi sometimes returns "Busy", what is wrong … and then even localized…
    while os == busytext.encode('utf-8'):
        os = xbmc.getInfoLabel('System.OsVersionInfo')
    kodi = 'Kodi/' + kodiversion
    oss = ' (' + os + ') ' + addonname + '/'
    addon.setSetting('os', oss)
    return kodi + oss + addonversion

def getCachedJson(url):
    headers = {
        "DNT": 1 if (setting('donottrack') == True) else 0,
        "X-UID": setting('user-id'),
        "User-Agent": getUserAgent(),
        "X-Resolution": xbmc.getInfoLabel('System.ScreenResolution').split('@')[0]
    }
    if not xbmcvfs.exists(cachedir):
        xbmcvfs.mkdirs(cachedir)

    if not xbmcvfs.exists(os.path.join(cachedir, 'etags.json')):
        etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'w')
        etagsf.write('{}')
        etagsf.close()

    etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'r')
    etags = json.loads(etagsf.read())
    etagsf.close()

    if url not in etags or 'etag' not in etags[url]:
        r = requests.get(url + '/', headers=headers)
        if 'Etag' in r.headers:
            etags[url] = {}
            etags[url]['path'] = cachedir + hashlib.md5(url).hexdigest() + '.json'
            etags[url]['etag'] = r.headers['Etag']

            f = xbmcvfs.File(etags[url]['path'], 'w')
            f.write(r.content)
            f.close()

        try:
            j = json.loads(r.content)
        except exceptions.ValueError:
            j = {}
    else:
        headers['If-None-Match'] = etags[url]['etag']
        r = requests.get(url + '/', headers=headers)
        if r.status_code == 304:
            etagsf = xbmcvfs.File(etags[url]['path'], 'r')
            j = json.loads(etagsf.read())
            etagsf.close()
        else:
            if 'Etag' in r.headers:
                etags[url]['path'] = cachedir + hashlib.md5(url).hexdigest() + '.json'
                etags[url]['etag'] = r.headers['Etag']

                f = xbmcvfs.File(etags[url]['path'], 'w')
                f.write(r.content)
                f.close()

            try:
                j = json.loads(r.content)
            except exceptions.ValueError:
                j = {}

    if j == {}:
        dialog = xbmcgui.Dialog()
        dialog.notification('Gronkh.DE', loc(30015), xbmcgui.NOTIFICATION_INFO, 5000)
        quit()
        return

    etagsf = xbmcvfs.File(os.path.join(cachedir, 'etags.json'), 'w')
    etagsf.write(json.dumps(etags))
    etagsf.close()

    return j

def makeTimeString(s):
    return str(int(s/60))

##### Functions
def checkVersion():
    versions = getCachedJson(API_URL + 'version')

    if API_VERSION == versions['current']:
        return

    if API_VERSION in versions['deprecated']:
        dialog = xbmcgui.Dialog()
        dialog.notification('Gronkh.DE', loc(30016), xbmcgui.NOTIFICATION_WARNING, 5000)
        return

    if API_VERSION in versions['deleted']:
        dialog = xbmcgui.Dialog()
        dialog.notification('Gronkh.DE', loc(30016), xbmcgui.NOTIFICATION_ERROR, 5000)
        quit()
        return

def index(a_slug=None):
    checkVersion()
    if a_slug:
        li = xbmcgui.ListItem(loc(30001))
        li.setIconImage(icondir + 'games.png')
        li.setThumbnailImage(icondir + 'games.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LPs', 'author' : a_slug}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30002))
        li.setIconImage(icondir + 'tests.png')
        li.setThumbnailImage(icondir + 'tests.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LTs', 'author' : a_slug}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)
    else:
        li = xbmcgui.ListItem(loc(30010))
        li.setIconImage(icondir + 'recent.png')
        li.setThumbnailImage(icondir + 'recent.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'recent'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30008))
        li.setIconImage(icondir + 'search.png')
        li.setThumbnailImage(icondir + 'search.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'search'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30007))
        li.setIconImage(icondir + 'live.png')
        li.setThumbnailImage(icondir + 'live.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'live'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30001))
        li.setIconImage(icondir + 'games.png')
        li.setThumbnailImage(icondir + 'games.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LPs'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30002))
        li.setIconImage(icondir + 'tests.png')
        li.setThumbnailImage(icondir + 'tests.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LTs'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

        li = xbmcgui.ListItem(loc(30003))
        li.setIconImage(icondir + 'authors.png')
        li.setThumbnailImage(icondir + 'authors.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'show_authors'}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def search():
    dialog = xbmcgui.Dialog()
    d = dialog.input(loc(30008), type=xbmcgui.INPUT_ALPHANUM)

    if not d:
        quit()

    result = getCachedJson(baseurl + "search/count/" + d)

    if result['lets-plays'] == 0 and result['tests'] == 0 and result['episodes'] == 0:
        dialog = xbmcgui.Dialog()
        dialog.notification('Gronkh.DE', loc(30014), xbmcgui.NOTIFICATION_INFO, 5000)
        quit()

    if result['lets-plays'] != 0:
        if result['lets-plays'] == 1:
            li = xbmcgui.ListItem(loc(30001) + ' (' + str(result['lets-plays']) + ' ' + loc(30013) + ')')
        else:
            li = xbmcgui.ListItem(loc(30001) + ' (' + str(result['lets-plays']) + ' ' + loc(30011) + ')')
        li.setIconImage(icondir + 'games.png')
        li.setThumbnailImage(icondir + 'games.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LPs', 'search' : d}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

    if result['tests'] != 0:
        if result['tests'] == 1:
            li = xbmcgui.ListItem(loc(30002) + ' (' + str(result['tests']) + ' ' + loc(30013) + ')')
        else:
            li = xbmcgui.ListItem(loc(30002) + ' (' + str(result['tests']) + ' ' + loc(30011) + ')')
        li.setIconImage(icondir + 'tests.png')
        li.setThumbnailImage(icondir + 'tests.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'LTs', 'search' : d}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

    if result['episodes'] != 0:
        if result['episodes'] == 1:
            li = xbmcgui.ListItem(loc(30012) + ' (' + str(result['episodes']) + ' ' + loc(30013) + ')')
        else:
            li = xbmcgui.ListItem(loc(30012) + ' (' + str(result['episodes']) + ' ' + loc(30011) + ')')
        li.setIconImage(icondir + 'episodes.png')
        li.setThumbnailImage(icondir + 'episodes.png')
        li.setArt({'fanart' : fanart})
        params = {'mode' : 'show_episodes', 'search' : d}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params), listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

def showAuthors():
    authors = getCachedJson(baseurl + 'authors')
    for aut in authors['authors']:
        li = xbmcgui.ListItem(aut['name'])
        li.setIconImage(aut['avatar'])
        li.setThumbnailImage(aut['avatar'])
        li.setArt({'fanart' : aut['fanart']})
        params = {'author' : aut['slug']}
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
            listitem=li, isFolder=True)
        xbmcplugin.addSortMethod(addon_handle,
            sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def showTests(a_slug=None, search=None):
    if a_slug:
        author = getCachedJson(baseurl + 'authors/' + a_slug)
        games = getCachedJson(baseurl + 'tests/' + a_slug)
        for game in games['tests']:
            li = xbmcgui.ListItem(game['gamename'])
            li.setIconImage(game['thumb'])
            li.setThumbnailImage(game['thumb'])
            params = {'mode' : 'play_video', 'type': 'test', 'slug' : game['slug']}
            li.setInfo('video', {
                                    'title' : game['gamename'],
                                    'episode': 1,
                                    'season': 1,
                                    'director': author['name'],
                                    'plot': game['description'],
                                    'rating': game['rating'],
                                    'duration': makeTimeString(game['duration']),
                                    'votes': str(game['votes']),
                                    'premiered': game['aired']
                                })
            li.setArt({'thumb': game['thumb'],
                        'poster': game['poster'],
                        'fanart': game['thumb']})
            li.setProperty('isPlayable','true')
            li.addStreamInfo('video', {'duration': game['duration']})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(addon_handle)
    elif search:
        auts = {}
        games = getCachedJson(baseurl + 'search/tests/' + search)
        for game in games['tests']:
            if game['author'] not in auts:
                auts[game['author']] = getCachedJson(baseurl + 'authors/' + game['author'])
            li = xbmcgui.ListItem(game['gamename'])
            li.setIconImage(game['thumb'])
            li.setThumbnailImage(game['thumb'])
            params = {'mode' : 'play_video', 'type': 'test', 'slug' : game['slug']}
            li.setInfo('video', {
                                    'title' : game['gamename'],
                                    'episode': 1,
                                    'season': 1,
                                    'director': auts[game['author']]['name'],
                                    'plot': game['description'],
                                    'rating': game['rating'],
                                    'duration': makeTimeString(game['duration']),
                                    'votes': str(game['votes']),
                                    'premiered': game['aired']
                                })
            li.setArt({'thumb': game['thumb'],
                        'poster': game['poster'],
                        'fanart': game['thumb']})
            li.setProperty('isPlayable','true')
            li.addStreamInfo('video', {'duration': game['duration']})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(addon_handle)
    else:
        auts = {}
        games = getCachedJson(baseurl + 'tests')
        for game in games['tests']:
            if game['author'] not in auts:
                auts[game['author']] = getCachedJson(baseurl + 'authors/' + game['author'])
            li = xbmcgui.ListItem(game['gamename'])
            li.setIconImage(game['thumb'])
            li.setThumbnailImage(game['thumb'])
            params = {'mode' : 'play_video', 'type': 'test', 'slug' : game['slug']}
            li.setInfo('video', {
                                    'title' : game['gamename'],
                                    'episode': 1,
                                    'season': 1,
                                    'director': auts[game['author']]['name'],
                                    'plot': game['description'],
                                    'rating': game['rating'],
                                    'duration': makeTimeString(game['duration']),
                                    'votes': str(game['votes']),
                                    'premiered': game['aired']
                                })
            li.setArt({'thumb': game['thumb'],
                        'poster': game['poster'],
                        'fanart': game['thumb']})
            li.setProperty('isPlayable','true')
            li.addStreamInfo('video', {'duration': game['duration']})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(addon_handle)

def showLPs(a_slug=None, search=None):
    if a_slug:
        games = getCachedJson(baseurl + 'lets-plays/' + a_slug)
        for lp in games['lets-plays']:
            li = xbmcgui.ListItem(lp['gamename'])
            li.setIconImage(lp['postersmall'])
            li.setThumbnailImage(lp['posterbig'])
            li.setArt({'fanart' : fanart})
            params = {'mode' : 'show_episodes', 'game' : lp['slug']}
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li, isFolder=True)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(addon_handle)
    elif search:
        auts = {}
        games = getCachedJson(baseurl + 'search/lets-plays/' + search)
        for lp in games['lets-plays']:
            if lp['author'] not in auts:
                auts[lp['author']] = getCachedJson(baseurl + 'authors/' + lp['author'])
            li = xbmcgui.ListItem(lp['gamename'] + ' (' + auts[lp['author']]['name'] + ')')
            li.setIconImage(lp['postersmall'])
            li.setThumbnailImage(lp['posterbig'])
            li.setArt({'fanart' : fanart})
            params = {'mode' : 'show_episodes', 'game' : lp['slug']}
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li, isFolder=True)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(addon_handle)
    else:
        auts = {}
        games = getCachedJson(baseurl + 'lets-plays')
        for lp in games['lets-plays']:
            if lp['author'] not in auts:
                auts[lp['author']] = getCachedJson(baseurl + 'authors/' + lp['author'])
            li = xbmcgui.ListItem(lp['gamename'] + ' (' + auts[lp['author']]['name'] + ')')
            li.setIconImage(lp['postersmall'])
            li.setThumbnailImage(lp['posterbig'])
            li.setArt({'fanart' : fanart})
            params = {'mode' : 'show_episodes', 'game' : lp['slug']}
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li, isFolder=True)
            xbmcplugin.addSortMethod(addon_handle,
                sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(addon_handle)

def showEpisodes(g_slug):
    lp = getCachedJson(baseurl + 'lets-play/' + g_slug)
    eps = getCachedJson(baseurl + 'episodes/' + g_slug)
    aut = getCachedJson(baseurl + 'authors/' + lp['author'])
    for ep in eps['episodes']:
        li = xbmcgui.ListItem(ep['episodename'].split(': ')[-1])
        li.setIconImage(ep['thumb'])
        li.setThumbnailImage(ep['thumb'])
        params = {'mode' : 'play_video', 'type' : 'episode', 'slug': ep['episodeslug']}
        li.setInfo('video', {
                                'title' : ep['episodename'].split(': ')[-1],
                                'originaltitle': lp['gamename'],
                                'episode': ep['episode'],
                                'season': 1,
                                'director': aut['name'],
                                'plot': ep['description'],
                                'rating': ep['rating'],
                                'duration': makeTimeString(ep['duration']),
                                'votes': str(ep['votes']),
                                'premiered': ep['aired']
                            })
        li.setArt({'thumb': ep['thumb'],
                    'poster': lp['posterbig'],
                    'fanart': ep['thumb']})
        li.setProperty('isPlayable','true')
        li.addStreamInfo('video', {'duration': ep['duration']})
        xbmcplugin.setContent(addon_handle, 'episodes')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
            listitem=li)
        xbmcplugin.addSortMethod(addon_handle,
            sortMethod=xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.endOfDirectory(addon_handle)

def showRecentEpisodes():
    lps = {}
    auts = {}
    episodes = getCachedJson(baseurl + 'recent')
    for ep in episodes['episodes']:
        if ep['gameslug'] not in lps:
            lps[ep['gameslug']] = getCachedJson(baseurl + 'lets-play/' + ep['gameslug'])
        if lps[ep['gameslug']]['author'] not in auts:
            auts[lps[ep['gameslug']]['author']] = getCachedJson(baseurl + 'authors/' + lps[ep['gameslug']]['author'])
        li = xbmcgui.ListItem(ep['episodename'].split(': ')[-1])
        li.setIconImage(ep['thumb'])
        li.setThumbnailImage(ep['thumb'])
        params = {'mode' : 'play_video', 'type' : 'episode', 'slug': ep['episodeslug']}
        li.setInfo('video', {
                                'title' : ep['episodename'].split(': ')[-1],
                                'originaltitle': lps[ep['gameslug']]['gamename'],
                                'episode': ep['episode'],
                                'season': 1,
                                'director': auts[lps[ep['gameslug']]['author']]['name'],
                                'plot': ep['description'],
                                'rating': ep['rating'],
                                'duration': makeTimeString(ep['duration']),
                                'votes': str(ep['votes']),
                                'premiered': ep['aired']
                            })
        li.setArt({'thumb': ep['thumb'],
                    'poster': lps[ep['gameslug']]['posterbig'],
                    'fanart': ep['thumb']})
        li.setProperty('isPlayable','true')
        li.addStreamInfo('video', {'duration': ep['duration']})
        xbmcplugin.setContent(addon_handle, 'episodes')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
            listitem=li)
        xbmcplugin.addSortMethod(addon_handle,
            sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(addon_handle)

def showSearchEpisodes(search):
    lps = {}
    auts = {}
    episodes = getCachedJson(baseurl + 'search/episodes/' + search)
    for ep in episodes['episodes']:
        if ep['gameslug'] not in lps:
            lps[ep['gameslug']] = getCachedJson(baseurl + 'lets-play/' + ep['gameslug'])
        if lps[ep['gameslug']]['author'] not in auts:
            auts[lps[ep['gameslug']]['author']] = getCachedJson(baseurl + 'authors/' + lps[ep['gameslug']]['author'])
        li = xbmcgui.ListItem(ep['episodename'].split(': ')[-1])
        li.setIconImage(ep['thumb'])
        li.setThumbnailImage(ep['thumb'])
        params = {'mode' : 'play_video', 'type' : 'episode', 'slug': ep['episodeslug']}
        li.setInfo('video', {
                                'title' : ep['episodename'].split(': ')[-1],
                                'originaltitle': lps[ep['gameslug']]['gamename'],
                                'episode': ep['episode'],
                                'season': 1,
                                'director': auts[lps[ep['gameslug']]['author']]['name'],
                                'plot': ep['description'],
                                'rating': ep['rating'],
                                'duration': makeTimeString(ep['duration']),
                                'votes': str(ep['votes']),
                                'premiered': ep['aired']
                            })
        li.setArt({'thumb': ep['thumb'],
                    'poster': lps[ep['gameslug']]['posterbig'],
                    'fanart': ep['thumb']})
        li.setProperty('isPlayable','true')
        li.addStreamInfo('video', {'duration': ep['duration']})
        xbmcplugin.setContent(addon_handle, 'episodes')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
            listitem=li)
        xbmcplugin.addSortMethod(addon_handle,
            sortMethod=xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(addon_handle)

def startVideo(t, s):
    if t == 'test':
        lt = getCachedJson(baseurl + 'test/' + s)
        aut = getCachedJson(baseurl + 'authors/' + lt['author'])

        li = xbmcgui.ListItem(lt['gamename'], path='plugin://plugin.video.youtube/play/?video_id=' + lt['youtube'])
        li.setIconImage(lt['thumb'])
        li.setThumbnailImage(lt['thumb'])
        li.setInfo('video', {
                                'title' : lt['gamename'],
                                'episode': 1,
                                'season': 1,
                                'director': aut['name'],
                                'plot': lt['description'],
                                'rating': lt['rating'],
                                'duration': makeTimeString(lt['duration']),
                                'votes': str(lt['votes']),
                                'premiered': lt['aired']
                            })
        li.setArt({'thumb': lt['thumb'],
                    'poster': lt['poster'],
                    'fanart': lt['thumb']})
        li.setProperty('isPlayable','true')
        li.addStreamInfo('video', {'duration': lt['duration']})
        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)
    else:
        ep = getCachedJson(baseurl + 'episode/' + s)
        lp = getCachedJson(baseurl + 'lets-play/' + ep['gameslug'])
        aut = getCachedJson(baseurl + 'authors/' + lp['author'])

        li = xbmcgui.ListItem(ep['episodename'].split(': ')[-1], path='plugin://plugin.video.youtube/play/?video_id=' + ep['youtube'])
        li.setIconImage(ep['thumb'])
        li.setThumbnailImage(ep['thumb'])
        li.setInfo('video', {
                                'title' : ep['episodename'].split(': ')[-1],
                                'originaltitle': lp['gamename'],
                                'episode': ep['episode'],
                                'season': 1,
                                'director': aut['name'],
                                'plot': ep['description'],
                                'tracknumber': ep['episode'],
                                'rating': ep['rating'],
                                'duration': makeTimeString(ep['duration']),
                                'votes': str(ep['votes']),
                                'premiered': ep['aired']
                            })
        li.setArt({'thumb': ep['thumb'],
                    'poster': lp['posterbig'],
                    'fanart': ep['thumb']})
        li.setProperty('isPlayable','true')
        li.addStreamInfo('video', {'duration': ep['duration']})
        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

def showLiveStreams():
    for name in twitchnames:
        r = requests.get(twitchStreamInfo + name, headers={'Accept': 'application/vnd.twitchtv.v3+json'})
        stream = json.loads(r.content)['stream']
        z = 0
        if stream:
            while 'bio' in stream['channel']:
                r = requests.get(twitchStreamInfo + name, headers={'Accept': 'application/vnd.twitchtv.v3+json'})
                stream = json.loads(r.content)['stream']
                z = z + 1
                if z > 5:
                    dialog = xbmcgui.Dialog()
                    dialog.notification('gronkh.DE', loc(30009), xbmcgui.NOTIFICATION_ERROR, 10000)
                    quit()
        if stream:
            li = None
            if stream['game']:
                li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + loc(30006) + ': ' + stream['game'])
            else:
                li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + stream['channel']['status'])
            li.setIconImage(stream['channel']['logo'] + '?' + unicode(time.time()))
            li.setThumbnailImage(stream['preview']['large'] + '?' + unicode(time.time()))
            li.setArt({ 'fanart' : stream['channel']['profile_banner'],
                        'clearlogo' : stream['channel']['logo'],
                        'banner' : stream['channel']['banner']})
            li.setInfo('video', {
                                    'director': stream['channel']['display_name'],
                                    'plotoutline': stream['channel']['status']
                                })
            li.setProperty('isPlayable','true')
            params = {'mode' : 'start_livestream', 'stream' : json.dumps(stream), 'name': name}
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li)
        else:
            li = xbmcgui.ListItem(u'[' + name + u'] – ' + loc(30005))
            li.setArt({ 'fanart' : fanart})
            li.setInfo('video', {
                                    'title' : u'[' + name + u'] – ' + loc(30005),
                                    'episode': 1,
                                    'season': 1,
                                    'director': name
                                })
            li.setProperty('isPlayable','true')
            params = {'mode' : 'start_livestream', 'stream' : json.dumps(stream), 'name': name}
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=makeUrl(params),
                listitem=li)
    xbmcplugin.addSortMethod(addon_handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(addon_handle)

def startLiveStream(stream, name):
    r = requests.get('https://api.twitch.tv/api/channels/' + name + '/access_token')
    j = json.loads(r.content)

    token   = j['token']
    sig     = j['sig']

    if stream:
            li = None
            if stream['game']:
                li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + loc(30006) + ': ' + stream['game'],
                    path='http://usher.twitch.tv/api/channel/hls/' +
                    name + '.m3u8?player=twitchweb&token=' +
                    token + '&sig=' +
                    sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
            else:
                li = xbmcgui.ListItem(stream['channel']['display_name'] + ' - ' + stream['channel']['status'],
                    path='http://usher.twitch.tv/api/channel/hls/' +
                    name + '.m3u8?player=twitchweb&token=' +
                    token + '&sig=' +
                    sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
            li.setIconImage(stream['channel']['logo'])
            li.setThumbnailImage(stream['preview']['large'] + '?' + unicode(time.time()))
            li.setArt({ 'fanart' : stream['channel']['profile_banner'],
                        'clearlogo' : stream['channel']['logo'],
                        'banner' : stream['channel']['banner']})
            li.setInfo('video', {
                                    'director': stream['channel']['display_name'],
                                    'plotoutline': stream['channel']['status']
                                })
            li.setProperty('isPlayable','true')
            xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)
    else:
        li = xbmcgui.ListItem(u'[' + name + u'] – ' + loc(30005),
            path='http://usher.twitch.tv/api/channel/hls/' +
            name + '.m3u8?player=twitchweb&token=' +
            token + '&sig=' +
            sig + '&allow_audio_only=true&allow_source=true&type=any&p=666')
        if stream:
            li.setIconImage(stream['preview']['medium'])
            li.setThumbnailImage(stream['preview']['large'])
        li.setArt({ 'fanart' : fanart})
        li.setInfo('video', {
                                'title' : u'[' + name + u'] – ' + loc(30005),
                                'episode': 1,
                                'season': 1,
                                'director': name
                            })
        li.setProperty('isPlayable','true')
        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

if 'mode' in params:
    if params['mode'][0] == 'show_authors':
        showAuthors()
    elif params['mode'][0] == 'search':
        search()
    elif params['mode'][0] == 'LTs':
        if 'author' in params:
            showTests(params['author'][0])
        elif 'search' in params:
            showTests(search=params['search'][0])
        else:
            showTests()
    elif params['mode'][0] == 'LPs':
        if 'author' in params:
            showLPs(params['author'][0])
        elif 'search' in params:
            showLPs(search=params['search'][0])
        else:
            showLPs()
    elif params['mode'][0] == 'show_episodes':
        if 'search' in params:
            showSearchEpisodes(params['search'][0])
        else:
            showEpisodes(params['game'][0])
    elif params['mode'][0] == 'play_video':
        startVideo(params['type'][0], params['slug'][0])
    elif params['mode'][0] == 'live':
        showLiveStreams()
    elif params['mode'][0] == 'start_livestream':
        startLiveStream(json.loads(params['stream'][0]), params['name'][0])
    elif params['mode'][0] == 'recent':
        showRecentEpisodes()
else:
    if 'author' in params:
        index(params['author'][0])
    else:
        index()
