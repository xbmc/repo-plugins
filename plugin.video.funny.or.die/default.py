import urllib
import urllib2
import re
import os
import htmlentitydefs
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup
import StorageServer

__settings__ = xbmcaddon.Addon(id='plugin.video.funny.or.die')
addon_version = __settings__.getAddonInfo('version')
__language__ = __settings__.getLocalizedString
home = xbmc.translatePath(__settings__.getAddonInfo('path'))
icon = os.path.join(home, 'icon.png')
next_png = os.path.join(home, 'resources', 'next.png')
cache = StorageServer.StorageServer("FunnyOrDie", 12)
# settings type changed, reset is needed for updates
if __settings__.getSetting('first_run') == 'true':
    __settings__.setSetting('sort_by', '0')
    __settings__.setSetting('sort_time', '0')
    __settings__.setSetting('first_run', 'false')


def addon_log(string):
        xbmc.log("[addon.funnyordie-%s]: %s" %(addon_version, string))

def make_request(url):
        try:
            headers = {
                'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
                'Referer' : 'http://www.funnyordie.com/videos'
                }
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' %e.code)
                xbmc.executebuiltin(
                    "XBMC.Notification(FunnyOrDie,HTTP ERROR: %s,5000,%s)"
                    %(e.code, icon)
                    )


def cache_categories():
        url = 'http://www.funnyordie.com/browse/videos/all/all/most_recent'
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'class' : 'dropdown'})[0]('a')
        cat_list = []
        for i in items:
            cat_list.append((i.string, i['href']))
        return cat_list


def get_categories():
        addDir(__language__(30024), 'search', 3, icon)
        sort = {
            '0': 'most_buzz',
            '1': 'most_recent',
            '2': 'most_viewed',
            '3': 'most_favorited',
            '4': 'highest_rated'
            }
        sort_t = {
            '0': '',
            '1': 'this_week',
            '2': 'this_month'
            }

        sort_by = sort[__settings__.getSetting('sort_by')]
        sort_time = sort_t[__settings__.getSetting('sort_time')]
        for i in cache.cacheFunction(cache_categories):
            url = 'http://www.funnyordie.com'
            url += '%s/%s/%s' %(i[1].rsplit('/', 1)[0], sort_by, sort_time)
            addDir(i[0], url, 1, icon)


## Thanks to Fredrik Lundh for this function - http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is
        return re.sub("&#?\w+;", fixup, text)


def index(url):
        data = make_request(url).replace("\\",'').replace('\n','').replace("\'",'')
        items = re.compile('<div class="detailed_vp">(.+?)</a>n</div></div>').findall(data)
        if len(items) < 1:
            items = re.compile('<div class="detailed_vp">(.+?)</a></div></div>').findall(data)
        for i in items:
            try:
                desc = unescape(re.findall('class="title" title="(.+?)"', i)[0])
            except:
                desc = ''
                addon_log('desc exception')
                continue
            name = desc.split(' from')[0]
            vid_id = re.findall('data-viewkey="(.+?)"', i)[0][1:]
            try:
                thumb = re.findall('class="thumbnail" src="(.+?)"', i)[0]
            except:
                thumb = ''
            try:
                duration = re.findall('<span class="duration">(.+?)</span>', i)[0]
            except:
                duration = ''
            addDir(name, vid_id, 2, thumb, duration, desc, True)

        try:
            page_num = re.findall('next_page = (.+?);', data)[0]
            page = '?page='+page_num
            if not '?page=' in url:
                page_url = None
                replace_list = ['exclusives', 'immortal']
                for i in replace_list:
                    if i in url:
                        page_url = url.replace('/all/', '/').replace('/videos/','/more/videos/all/')
                if not page_url:
                        page_url = url.replace('/videos/','/more/videos/')
                if __settings__.getSetting('sort_time') == '0':
                    page_url += 'all_time'
                page_url += page
            else:
                page_url = url.split('?page')[0]+page
            addDir(__language__(30031), page_url, 1, next_png)
        except:
            addon_log('nextpage exception')


def playVid(url):
        url = 'http://vo.fod4.com/v/%s/v600.mp4' %url
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def search(search_url):
        if search_url == 'search':
            keyboard = xbmc.Keyboard('', __language__(30006))
            keyboard.doModal()
            if keyboard.isConfirmed() == False:
                return
            search_query = keyboard.getText()
            if len(search_query) == 0:
                return
            search_url = 'http://www.funnyordie.com/search/a/videos?q='+urllib.quote_plus(search_query)
        soup = BeautifulSoup(make_request(search_url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        search_results = soup.findAll('div', attrs={'class': "box search_results_box"})[0]('div', attrs={'class': 'details '})
        for i in search_results:
            # href = i.a['href']
            title = i.a['title'].encode('utf-8')
            try: duration = i.find('span', attrs={'class': 'duration'}).string
            except: duration = ''
            thumb = i.findPrevious('a', attrs={'class': 'nail'}).img['src']
            vid_key = i.findPrevious('h2').findPrevious('div')['data-viewkey'][1:]
            addDir(title, vid_key, 2, thumb, duration, '', True)
        page = soup.find('a', attrs={'rel': 'next'})
        if page:
            page_url = 'http://www.funnyordie.com'+page['href']
            addDir(__language__(30031), page_url, 3, next_png)


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]

        return param


def addDir(name,url,mode,iconimage,duration='',desc='',isplayable=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        isfolder = True
        if isplayable:
            liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": duration, "Plot": desc})
            liz.setProperty('IsPlayable', 'true')
            isfolder = False
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isfolder)
        return ok


params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    get_categories()

elif mode==1:
    index(url)

elif mode==2:
    playVid(url)

elif mode==3:
    search(url)

xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))