'''
    Dailymotion_com

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

import six
from kodi_six import xbmcplugin, xbmcaddon, xbmcgui, xbmc, xbmcvfs
import sys
import re
import json
import datetime
import tempfile
import requests
from six.moves import urllib_parse, html_parser

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
_icon = addon.getAddonInfo('icon')
_fanart = addon.getAddonInfo('fanart')
_path = addon.getAddonInfo('path')
_ipath = '{0}/resources/images/'.format(_path)

if hasattr(xbmcvfs, "translatePath"):
    translate_path = xbmcvfs.translatePath
else:
    translate_path = xbmc.translatePath
channelFavsFile = translate_path("special://profile/addon_data/{0}/{0}.favorites".format(addonID))
HistoryFile = translate_path("special://profile/addon_data/{0}/{0}.history".format(addonID))
cookie_file = translate_path("special://profile/addon_data/{0}/cookies".format(addonID))
pDialog = xbmcgui.DialogProgress()
familyFilter = '1'

if not xbmcvfs.exists('special://profile/addon_data/' + addonID + '/settings.xml'):
    addon.openSettings()

if addon.getSetting('family_filter') == 'false':
    familyFilter = '0'

force_mode = addon.getSetting("forceViewMode") == "true"
if force_mode:
    menu_mode = addon.getSetting("MenuMode")
    video_mode = addon.getSetting("VideoMode")

maxVideoQuality = addon.getSetting("maxVideoQuality")
downloadDir = addon.getSetting("downloadDir")
qual = ['240', '380', '480', '720', '1080', '1440', '2160']
maxVideoQuality = qual[int(maxVideoQuality)]
language = addon.getSetting("language")
languages = ["ar_ES", "br_PT", "ca_EN", "ca_FR", "de_DE", "es_ES", "fr_FR",
             "in_EN", "id_ID", "it_IT", "ci_FR", "my_MS", "mx_ES", "pk_EN",
             "ph_EN", "tr_TR", "en_GB", "en_US", "vn_VI", "kr_KO", "tw_TW"]
language = languages[int(language)]
dmUser = addon.getSetting("dmUser")
itemsPerPage = addon.getSetting("itemsPerPage")
itemsPage = ["25", "50", "75", "100"]
itemsPerPage = itemsPage[int(itemsPerPage)]
urlMain = "https://api.dailymotion.com"
_UA = 'Mozilla/5.0 (Linux; Android 7.1.1; Pixel Build/NMF26O) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.91 Mobile Safari/537.36'


class MLStripper(html_parser.HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    parser = html_parser.HTMLParser()
    html = parser.unescape(html)
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def strip_tags2(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def index():
    addDir(translation(30025), "{0}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&list=what-to-watch&no_live=1&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'listVideos', "{0}what_to_watch.png".format(_ipath))
    addDir(translation(30015), "{0}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=trending&no_live=1&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'listVideos', "{0}trending.png".format(_ipath))
    addDir(translation(30016), "{0}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&featured=1&no_live=1&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'listVideos', "{0}featured.png".format(_ipath))
    addDir(translation(30003), "{0}/videos?fields=id,thumbnail_large_url,title,views_last_hour&availability=1&live_onair=1&sort=visited-month&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'listLive', "{0}live.png".format(_ipath))
    addDir(translation(30006), "", 'listChannels', "{0}channels.png".format(_ipath))
    addDir(translation(30007), "{0}/users?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'listUsers', "{0}users.png".format(_ipath))
    addDir(translation(30002), "{0}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&search=&sort=relevance&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language), 'search', "{0}search.png".format(_ipath))
    addDir("{0} {1}".format(translation(30002), translation(30003)), "", 'livesearch', "{0}search_live.png".format(_ipath))
    addDir("{0} {1}".format(translation(30002), translation(30007)), "", 'usersearch', "{0}search_users.png".format(_ipath))
    addDir(translation(30115), "", "History", "{0}search.png".format(_ipath))
    if dmUser:
        addDir(translation(30034), "", "personalMain", "{0}my_stuff.png".format(_ipath))
    else:
        addFavDir(translation(30024), "", "favouriteUsers", "{0}favourite_users.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, "addons")
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def personalMain():
    addDir(translation(30041), "{0}/user/{1}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, dmUser, itemsPerPage, familyFilter, language), 'listVideos', "{0}videos.png".format(_ipath))
    addDir(translation(30035), "{0}/user/{1}/following?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, dmUser, itemsPerPage, familyFilter, language), 'listUsers', "{0}contacts.png".format(_ipath))
    addDir(translation(30036), "{0}/user/{1}/subscriptions?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, dmUser, itemsPerPage, familyFilter, language), 'listVideos', "{0}following.png".format(_ipath))
    addDir(translation(30037), "{0}/user/{1}/favorites?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, dmUser, itemsPerPage, familyFilter, language), 'listVideos', "{0}favourites.png".format(_ipath))
    addDir(translation(30038), "{0}/user/{1}/playlists?fields=id,name,videos_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, dmUser, itemsPerPage, familyFilter, language), 'listUserPlaylists', "{0}playlists.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, 'addons')
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def listUserPlaylists(url):
    content = getUrl2(url)
    content = json.loads(content)
    for item in content['list']:
        vid = item['id']
        title = item['name'].encode('utf-8') if six.PY2 else item['name']
        vids = item['videos_total']
        addDir("{0} ({1})".format(title, vids), urllib_parse.quote_plus("{0}_{1}_{2}".format(vid, dmUser, title)), 'showPlaylist', "{0}playlists.png".format(_ipath))
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage + 1
        addDir("{0} ({1})".format(translation(30001), nextPage), url.replace("page={0}".format(currentPage), "page={0}".format(nextPage)), 'listUserPlaylists', "{0}next_page2.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, "episodes")
    xbmcplugin.endOfDirectory(pluginhandle)


def showPlaylist(pid):
    url = "{0}/playlist/{1}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, pid, itemsPerPage, familyFilter, language)
    listVideos(url)


def favouriteUsers():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if xbmcvfs.exists(channelFavsFile):
        with open(channelFavsFile, 'r') as fh:
            content = fh.read()
            match = re.compile('###USER###=(.+?)###THUMB###=(.*?)###END###', re.DOTALL).findall(content)
            for user, thumb in match:
                addUserFavDir(user, 'owner:{0}'.format(user), 'sortVideos1', thumb)
    xbmcplugin.setContent(pluginhandle, "addons")
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def listChannels():
    content = getUrl2("{0}/channels?family_filter={1}&localization={2}".format(urlMain, familyFilter, language))
    content = json.loads(content)
    for item in content['list']:
        cid = item['id']
        title = item['name'].encode('utf-8') if six.PY2 else item['name']
        desc = item['description'].encode('utf-8') if six.PY2 else item['description']
        addDir(title, 'channel:{0}'.format(cid), 'sortVideos1', '{0}channels.png'.format(_ipath), desc)
    xbmcplugin.endOfDirectory(pluginhandle)


def sortVideos1(url):
    item_type = url[:url.find(":")]
    gid = url[url.find(":") + 1:]
    if item_type == "group":
        url = "{0}/group/{1}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, gid, itemsPerPage, familyFilter, language)
    else:
        url = "{0}/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&{1}={2}&sort=recent&limit={3}&family_filter={4}&localization={5}&page=1".format(urlMain, item_type, gid, itemsPerPage, familyFilter, language)
    addDir(translation(30015), url.replace("sort=recent", "sort=trending"), 'listVideos', "{0}trending.png".format(_ipath))
    addDir(translation(30008), url, 'listVideos', "{0}most_recent.png".format(_ipath))
    addDir(translation(30009), url.replace("sort=recent", "sort=visited"), 'sortVideos2', "{0}most_viewed.png".format(_ipath))
    if item_type == "owner":
        addDir("- {0}".format(translation(30038)), "{0}/user/{1}/playlists?fields=id,name,videos_total&sort=recent&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, gid, itemsPerPage, familyFilter, language), 'listUserPlaylists', "{0}playlists.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, 'addons')
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def sortVideos2(url):
    addDir(translation(30010), url.replace("sort=visited", "sort=visited-hour"), "listVideos", "{0}most_viewed.png".format(_ipath))
    addDir(translation(30011), url.replace("sort=visited", "sort=visited-today"), "listVideos", "{0}most_viewed.png".format(_ipath))
    addDir(translation(30012), url.replace("sort=visited", "sort=visited-week"), "listVideos", "{0}most_viewed.png".format(_ipath))
    addDir(translation(30013), url.replace("sort=visited", "sort=visited-month"), "listVideos", "{0}most_viewed.png".format(_ipath))
    addDir(translation(30014), url, 'listVideos', "{0}most_viewed.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, 'addons')
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def sortUsers1():
    url = "{0}/users?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit={1}&family_filter={2}&localization={3}&page=1".format(urlMain, itemsPerPage, familyFilter, language)
    addDir(translation(30040), url, 'sortUsers2', "")
    addDir(translation(30016), "{0}&filters=featured".format(url), 'sortUsers2', "")
    addDir(translation(30017), "{0}&filters=official".format(url), 'sortUsers2', "")
    addDir(translation(30018), "{0}&filters=creative".format(url), 'sortUsers2', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def sortUsers2(url):
    addDir(translation(30019), url, 'listUsers', "")
    addDir(translation(30020), url.replace("sort=popular", "sort=commented"), 'listUsers', "")
    addDir(translation(30021), url.replace("sort=popular", "sort=rated"), 'listUsers', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    xbmcplugin.setContent(pluginhandle, 'episodes')
    content = getUrl2(url)
    content = json.loads(content)
    count = 1
    for item in content['list']:
        vid = item['id']
        title = item['title'].encode('utf-8') if six.PY2 else item['title']
        desc = strip_tags(item['description']).encode('utf-8') if six.PY2 else strip_tags2(item['description'])
        duration = item['duration']
        user = item['owner.username']
        date = item['taken_time']
        thumb = item['thumbnail_large_url']
        views = item['views_total']
        try:
            date = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
        except:
            date = ""
        temp = ("User: {0}  |  {1} Views  |  {2}".format(user, views, date))
        temp = temp.encode('utf-8') if six.PY2 else temp
        try:
            desc = "{0}\n{1}".format(temp, desc)
        except:
            desc = ""
        if user == "hulu":
            pass
        elif user == "cracklemovies":
            pass
        elif user == "ARTEplus7":
            addLink(title, vid, 'playArte', thumb.replace("\\", ""), user, desc, duration, date, count)
            count += 1
        else:
            addLink(title, vid, 'playVideo', thumb.replace("\\", ""), user, desc, duration, date, count)
            count += 1
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage + 1
        addDir("{0} ({1})".format(translation(30001), nextPage), url.replace("page={0}".format(currentPage), "page={0}".format(nextPage)), 'listVideos', "{0}next_page2.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, "episodes")
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(video_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def listUsers(url):
    content = getUrl2(url)
    content = json.loads(content)
    for item in content['list']:
        if item['username']:
            user = item['username'].encode('utf-8') if six.PY2 else item['username']
            thumb = item['avatar_large_url']
            videos = item['videos_total']
            views = item['views_total']
            addUserDir(user, 'owner:{0}'.format(user), 'sortVideos1', thumb.replace("\\", ""), "Views: {0}\nVideos: {1}".format(views, videos))
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage + 1
        addDir("{0} ({1})".format(translation(30001), nextPage), url.replace("page={0}".format(currentPage), "page={0}".format(nextPage)), 'listUsers', "{0}next_page.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, "addons")
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def listLive(url):
    content = getUrl2(url)
    content = json.loads(content)
    for item in content['list']:
        title = item['title'].encode('utf-8') if six.PY2 else item['title']
        vid = item['id']
        thumb = item['thumbnail_large_url']
        views = item['views_last_hour']
        addLiveLink(title, vid, 'playLiveVideo', thumb.replace("\\", ""), views)
    if content['has_more']:
        currentPage = content['page']
        nextPage = currentPage + 1
        addDir("{0} ({1})".format(translation(30001), nextPage), url.replace("page={0}".format(currentPage), "page={0}".format(nextPage)), 'listLive', "{0}next_page2.png".format(_ipath))
    xbmcplugin.setContent(pluginhandle, "episodes")
    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(vid, live=False):
    if live:
        url = getStreamUrl(vid, live=True)
    else:
        url = getStreamUrl(vid)
    xbmc.log("DAILYMOTION - FinalUrl = {0}".format(url), xbmc.LOGDEBUG)

    if url:
        listitem = xbmcgui.ListItem(path=url)
        if '.m3u8' in url:
            listitem.setMimeType("application/x-mpegURL")
        else:
            listitem.setMimeType("video/mp4")
        listitem.setContentLookup(False)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=listitem)
    else:
        xbmcgui.Dialog().notification('Info:', translation(30022), _icon, 5000, False)


def s(elem):
    if elem[0] == "auto":
        return 1
    else:
        return int(elem[0].split("@")[0])


def getStreamUrl(vid, live=False):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    xbmc.log('DAILYMOTION - url is {0}'.format(url), xbmc.LOGDEBUG)
    headers = {'User-Agent': _UA,
               'Origin': 'https://www.dailymotion.com',
               'Referer': 'https://www.dailymotion.com/'}
    cookie = {'lang': language,
              'ff': ff}
    r = requests.get("https://www.dailymotion.com/player/metadata/video/{0}".format(vid), headers=headers, cookies=cookie)
    content = r.json()
    if content.get('error') is not None:
        Error = (content['error']['title'])
        xbmcgui.Dialog().notification('Info:', Error, _icon, 5000, False)
        return
    else:
        cc = content['qualities']
        cc = list(cc.items())
        cc = sorted(cc, key=s, reverse=True)
        m_url = ''
        other_playable_url = []

        for source, json_source in cc:
            source = source.split("@")[0]
            for item in json_source:
                m_url = item.get('url', None)
                xbmc.log("DAILYMOTION - m_url = {0}".format(m_url), xbmc.LOGDEBUG)
                if m_url:
                    if not live:
                        if source == "auto":
                            mbtext = requests.get(m_url, headers=headers).text
                            mb = re.findall('NAME="([^"]+)",PROGRESSIVE-URI="([^"]+)"', mbtext)
                            if checkUrl(mb[-1][1].split('#cell')[0]) is False:
                                mb = re.findall(r'NAME="([^"]+)".+\n([^\n]+)', mbtext)
                            mb = sorted(mb, key=s, reverse=True)
                            for quality, strurl in mb:
                                quality = quality.split("@")[0]
                                if int(quality) <= int(maxVideoQuality):
                                    strurl = '{0}|{1}'.format(strurl.split('#cell')[0], urllib_parse.urlencode(headers))
                                    xbmc.log('Selected URL is: {0}'.format(strurl), xbmc.LOGDEBUG)
                                    return strurl

                        elif int(source) <= int(maxVideoQuality):
                            if 'video' in item.get('type', None):
                                return '{0}|{1}'.format(m_url, urllib_parse.urlencode(headers))

                    else:
                        m_url = m_url.replace('dvr=true&', '')
                        if '.m3u8?sec' in m_url:
                            m_url1 = m_url.split('?sec=')
                            the_url = '{0}?redirect=0&sec={1}'.format(m_url1[0], urllib_parse.quote(m_url1[1]))
                            rr = requests.get(the_url, cookies=r.cookies.get_dict(), headers=headers)
                            if rr.status_code > 200:
                                rr = requests.get(m_url, cookies=r.cookies.get_dict(), headers=headers)
                            mb = re.findall('NAME="([^"]+)"\n(.+)', rr.text)
                            mb = sorted(mb, key=s, reverse=True)
                            for quality, strurl in mb:
                                quality = quality.split("@")[0]
                                if int(quality) <= int(maxVideoQuality):
                                    if not strurl.startswith('http'):
                                        strurl1 = re.findall('(.+/)', the_url)[0]
                                        strurl = strurl1 + strurl
                                    strurl = '{0}|{1}'.format(strurl.split('#cell')[0], urllib_parse.urlencode(headers))
                                    xbmc.log('Selected URL is: {0}'.format(strurl), xbmc.LOGDEBUG)
                                    return strurl
                    if type(m_url) is list:
                        m_url = '?sec='.join(m_url)
                    other_playable_url.append(m_url)

        if len(other_playable_url) > 0:  # probably not needed, only for last resort
            for m_url in other_playable_url:
                xbmc.log("DAILYMOTION - other m_url = {0}".format(m_url), xbmc.LOGDEBUG)
                m_url = m_url.replace('dvr=true&', '')
                if '.m3u8?sec' in m_url:
                    rr = requests.get(m_url, cookies=r.cookies.get_dict(), headers=headers)
                    mburl = re.findall('(http.+)', rr.text)[0].split('#cell')[0]
                    if rr.headers.get('set-cookie'):
                        xbmc.log('DAILYMOTION - adding cookie to url', xbmc.LOGDEBUG)
                        strurl = '{0}|Cookie={1}'.format(mburl, rr.headers['set-cookie'])
                    else:
                        mb = requests.get(mburl, headers=headers).text
                        mb = re.findall('NAME="([^"]+)"\n(.+)', mb)
                        mb = sorted(mb, key=s, reverse=True)
                        for quality, strurl in mb:
                            quality = quality.split("@")[0]
                            if int(quality) <= int(maxVideoQuality):
                                if not strurl.startswith('http'):
                                    strurl1 = re.findall('(.+/)', mburl)[0]
                                    strurl = strurl1 + strurl
                                break

                    xbmc.log("DAILYMOTION - Calculated url = {0}".format(strurl), xbmc.LOGDEBUG)
                    return strurl


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def downloadVideo(title, vid):
    global downloadDir
    if not downloadDir:
        xbmcgui.Dialog().notification('Download:', translation(30110), _icon, 5000, False)
        return
    url, hstr = getStreamUrl(vid).split('|')
    if six.PY2:
        vidfile = xbmc.makeLegalFilename((downloadDir + title.decode('utf-8') + '.mp4').encode('utf-8'))
    else:
        vidfile = xbmcvfs.makeLegalFilename(downloadDir + title + '.mp4')
    if not xbmcvfs.exists(vidfile):
        tmp_file = tempfile.mktemp(dir=downloadDir, suffix='.mp4')
        if six.PY2:
            tmp_file = xbmc.makeLegalFilename(tmp_file)
        else:
            tmp_file = xbmcvfs.makeLegalFilename(tmp_file)
        pDialog.create('Dailymotion', '{0}[CR]{1}'.format(translation(30044), title))
        dfile = requests.get(url, headers=dict(urllib_parse.parse_qsl(hstr)), stream=True)
        totalsize = float(dfile.headers['content-length'])
        handle = open(tmp_file, "wb")
        chunks = 0
        for chunk in dfile.iter_content(chunk_size=2097152):
            if chunk:  # filter out keep-alive new chunks
                handle.write(chunk)
                chunks += 1
                percent = int(float(chunks * 209715200) / totalsize)
                pDialog.update(percent)
                if pDialog.iscanceled():
                    handle.close()
                    xbmcvfs.delete(tmp_file)
                    break
        handle.close()
        try:
            xbmcvfs.rename(tmp_file, vidfile)
            return vidfile
        except:
            return tmp_file
    else:
        xbmcgui.Dialog().notification('Download:', translation(30109), _icon, 5000, False)


def playArte(aid):
    try:
        content = getUrl2("http://www.dailymotion.com/video/{0}".format(aid))
        match = re.compile(r'<a\s*class="link"\s*href="http://videos.arte.tv/(.+?)/videos/(.+?).html">', re.DOTALL).findall(content)
        lang = match[0][0]
        vid = match[0][1]
        url = "http://videos.arte.tv/{0}/do_delegate/videos/{1},view,asPlayerXml.xml".format(lang, vid)
        content = getUrl2(url)
        match = re.compile(r'<video\s*lang="{0}"\s*ref="(.+?)"'.format(lang), re.DOTALL).findall(content)
        url = match[0]
        content = getUrl2(url)
        match1 = re.compile(r'<url\s*quality="hd">(.+?)</url>', re.DOTALL).findall(content)
        match2 = re.compile(r'<url\s*quality="sd">(.+?)</url>', re.DOTALL).findall(content)
        urlNew = ""
        if match1:
            urlNew = match1[0]
        elif match2:
            urlNew = match2[0]
        urlNew = urlNew.replace("MP4:", "mp4:")
        base = urlNew[:urlNew.find("mp4:")]
        playpath = urlNew[urlNew.find("mp4:"):]
        listitem = xbmcgui.ListItem(path="{0} playpath={1} swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_24-3188338-data-5168030.swf".format(base, playpath))
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    except:
        xbmcgui.Dialog().notification('Info:', translation(30110) + ' (Arte)!', _icon, 5000, False)


def addFav():
    keyboard = xbmc.Keyboard('', translation(30033))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        user = keyboard.getText()
        channelEntry = "###USER###={0}###THUMB###=###END###".format(user)
        if xbmcvfs.exists(channelFavsFile):
            with open(channelFavsFile, 'r') as fh:
                content = fh.read()
            if content.find(channelEntry) == -1:
                with open(channelFavsFile, 'a') as fh:
                    fh.write(channelEntry + "\n")
        else:
            with open(channelFavsFile, 'a') as fh:
                fh.write(channelEntry + "\n")
        xbmcgui.Dialog().notification('Info:', translation(30030), _icon, 5000, False)


def favourites(param):
    mode = param[param.find("###MODE###=") + 11:]
    mode = mode[:mode.find("###")]
    channelEntry = param[param.find("###USER###="):]
    user = param[11 + param.find("###USER###="):param.find("###THUMB###")]
    user = user.encode('utf8') if six.PY2 else user
    if mode == "ADD":
        if xbmcvfs.exists(channelFavsFile):
            with open(channelFavsFile, 'r') as fh:
                content = fh.read()
            if content.find(channelEntry) == -1:
                with open(channelFavsFile, 'a') as fh:
                    fh.write(channelEntry + "\n")
        else:
            with open(channelFavsFile, 'a') as fh:
                fh.write(channelEntry + "\n")
            fh.close()
        xbmcgui.Dialog().notification('Info:', '{0} {1}!'.format(user, translation(30030)), _icon, 5000, False)
    elif mode == "REMOVE":
        refresh = param[param.find("###REFRESH###=") + 14:]
        refresh = refresh[:refresh.find("###USER###=")]
        with open(channelFavsFile, 'r') as fh:
            content = fh.read()
        # entry = content[content.find(channelEntry):]
        with open(channelFavsFile, 'w') as fh:
            fh.write(content.replace(channelEntry + "\n", ""))
        if refresh == "TRUE":
            xbmc.executebuiltin("Container.Refresh")


def translation(lid):
    return addon.getLocalizedString(lid).encode('utf-8') if six.PY2 else addon.getLocalizedString(lid)


def getUrl2(url):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    xbmc.log('DAILYMOTION - The url is {0}'.format(url), xbmc.LOGDEBUG)
    headers = {'User-Agent': _UA}
    cookie = {'lang': language,
              'ff': ff}
    r = requests.get(url, headers=headers, cookies=cookie)
    return r.text


def checkUrl(url):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    xbmc.log('DAILYMOTION - Check url is {0}'.format(url), xbmc.LOGDEBUG)
    headers = {'User-Agent': _UA,
               'Referer': 'https://www.dailymotion.com/',
               'Origin': 'https://www.dailymotion.com'}
    cookie = {'lang': language,
              'ff': ff}
    r = requests.head(url, headers=headers, cookies=cookie)
    status = r.status_code == 200
    return status


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, user, desc, duration, date, nr):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Aired": date, "Duration": duration, "Episode": nr})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    entries.append((translation(30044), 'RunPlugin(plugin://{0}/?mode=downloadVideo&name={1}&url={2})'.format(addonID, urllib_parse.quote_plus(name), urllib_parse.quote_plus(url)),))
    entries.append((translation(30043), 'RunPlugin(plugin://{0}/?mode=queueVideo&url={1}&name={2})'.format(addonID, urllib_parse.quote_plus(u), urllib_parse.quote_plus(name)),))
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###={0}###THUMB###=DefaultVideo.png###END###".format(user)
        entries.append((translation(30028), 'RunPlugin(plugin://{0}/?mode=favourites&url={1})'.format(addonID, urllib_parse.quote_plus(playListInfos)),))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addLiveLink(name, url, mode, iconimage, desc):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserDir(name, url, mode, iconimage, desc):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###={0}###THUMB###={1}###END###".format(name, iconimage)
        liz.addContextMenuItems([(translation(30028), 'RunPlugin(plugin://{0}/?mode=favourites&url={1})'.format(addonID, urllib_parse.quote_plus(playListInfos)),)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addFavDir(name, url, mode, iconimage):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30033), 'RunPlugin(plugin://{0}/?mode=addFav)'.format('addonID'),)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserFavDir(name, url, mode, iconimage):
    u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib_parse.quote_plus(url), mode)
    ok = True
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage,
                'icon': _icon,
                'poster': iconimage,
                'fanart': _fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if dmUser == "":
        playListInfos = "###MODE###=REMOVE###REFRESH###=TRUE###USER###={0}###THUMB###={1}###END###".format(name, iconimage)
        liz.addContextMenuItems([(translation(30029), 'RunPlugin(plugin://{0}/?mode=favourites&url={1})'.format(addonID, urllib_parse.quote_plus(playListInfos)),)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def get_key(heading):
    keyboard = xbmc.Keyboard('', heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()


def search(url):
    search_string = get_key(translation(30002))
    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=False)
    if search_string and len(search_string) > 2:
        url2 = url.replace("&search=", "&search={0}".format(urllib_parse.quote_plus(search_string)))
        addtoHistory({'name': search_string, 'url': urllib_parse.quote_plus(url2), 'mode': 'listVideos'})
        u = "{0}?url={1}&mode=listVideos".format(sys.argv[0], urllib_parse.quote_plus(url2))
        xbmc.executebuiltin("Container.Update({0})".format(u))
    else:
        xbmc.executebuiltin("Container.Update({0},replace)".format(sys.argv[0]))


def searchLive():
    keyboard = xbmc.Keyboard('', '{0} {1}'.format(translation(30002), translation(30003)))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        searchl_string = urllib_parse.quote_plus(keyboard.getText())
        listLive("{0}/videos?fields=id,thumbnail_large_url,title,views_last_hour&live_onair=1&search={1}&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, searchl_string, itemsPerPage, familyFilter, language))


def searchUser():
    keyboard = xbmc.Keyboard('', translation(30002) + ' ' + translation(30007))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        searchl_string = urllib_parse.quote_plus(keyboard.getText())
        listUsers("{0}/users?fields=username,avatar_large_url,videos_total,views_total&search={1}&limit={2}&family_filter={3}&localization={4}&page=1".format(urlMain, searchl_string, itemsPerPage, familyFilter, language))


def addtoHistory(item):
    if xbmcvfs.exists(HistoryFile):
        with open(HistoryFile, 'r') as fh:
            content = fh.read()
        if content.find(item["url"]) == -1:  # use url to verify
            with open(HistoryFile, 'a') as fh:
                fh.write(json.dumps(item) + "\n")
    else:
        with open(HistoryFile, 'a') as fh:
            fh.write(json.dumps(item) + "\n")


def History():
    if xbmcvfs.exists(HistoryFile):
        with open(HistoryFile, 'r') as fh:
            content = fh.readlines()
            if len(content) > 0:
                content = [json.loads(x) for x in content]
                reversed_content = content[::-1]  # reverse order
                addHistoryDir(reversed_content)
                addDir("[COLOR red]{0}[/COLOR]".format(translation(30116)), "", "delHistory", "{0}search.png".format(_ipath))
                xbmcplugin.setContent(pluginhandle, "addons")

    if force_mode:
        xbmc.executebuiltin('Container.SetViewMode({0})'.format(menu_mode))

    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=False)


def delHistory():
    if xbmcgui.Dialog().yesno("Dailymotion", "Clear all search terms?"):
        with open(HistoryFile, 'w') as fh:
            fh.write("")


def addHistoryDir(listofdicts):
    listoflists = []

    for item in listofdicts:
        list_item = xbmcgui.ListItem(label=item["name"])
        list_item.setArt({"thumb": "{0}search.png".format(_ipath),
                          "icon": "{0}search.png".format(_ipath)})
        list_item.setInfo(type="Video", infoLabels={"genre": "History"})
        url = "{0}?url={1}&mode={2}".format(sys.argv[0], item["url"], item["mode"])

        listoflists.append((url, list_item, True))

    ok = xbmcplugin.addDirectoryItems(pluginhandle, listoflists, len(listoflists))
    return ok


params = parameters_string_to_dict(sys.argv[2])
mode = urllib_parse.unquote_plus(params.get('mode', ''))
url = urllib_parse.unquote_plus(params.get('url', ''))
name = urllib_parse.unquote_plus(params.get('name', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLive':
    listLive(url)
elif mode == 'listUsers':
    listUsers(url)
elif mode == 'listChannels':
    listChannels()
elif mode == 'favourites':
    favourites(url)
elif mode == 'addFav':
    addFav()
elif mode == 'personalMain':
    personalMain()
elif mode == 'favouriteUsers':
    favouriteUsers()
elif mode == 'listUserPlaylists':
    listUserPlaylists(url)
elif mode == 'showPlaylist':
    showPlaylist(url)
elif mode == 'sortVideos1':
    sortVideos1(url)
elif mode == 'sortVideos2':
    sortVideos2(url)
elif mode == 'sortUsers1':
    sortUsers1()
elif mode == 'sortUsers2':
    sortUsers2(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playLiveVideo':
    playVideo(url, live=True)
elif mode == 'playArte':
    playArte(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == "downloadVideo":
    downloadVideo(name, url)
elif mode == 'search':
    search(url)
elif mode == 'livesearch':
    searchLive()
elif mode == 'usersearch':
    searchUser()
elif mode == 'History':
    History()
elif mode == 'delHistory':
    delHistory()
else:
    index()
