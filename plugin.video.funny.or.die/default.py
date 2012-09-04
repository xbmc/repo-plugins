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
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by').replace(' ','_').lower()
sort_time = __settings__.getSetting('sort_time').replace(' ','_').lower()
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
cache = StorageServer.StorageServer("FunnyOrDie", 24)


def make_request(url, headers=None):
        try:
            if headers is None:
                headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                           'Referer' : 'http://www.funnyordie.com/videos'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification(FunnyOrDie,HTTP ERROR: "+str(e.code)+",5000,"+icon+")")


def cache_categories():
        soup = BeautifulSoup(make_request('http://www.funnyordie.com/browse/videos/all/all/most_buzz'))
        items = soup('div', attrs={'class' : 'dropdown'})[0]('a')
        cat_list = []
        for i in items:
            cat_list.append((i.string, i['href']))
        return cat_list


def get_categories():
        for i in cache.cacheFunction(cache_categories):
            url = 'http://www.funnyordie.com/'
            url += '%s/%s/%s' %(i[1].rsplit('/', 1)[0], sort, sort_time)
            addDir(i[0],url,1,icon)


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
                print '--desc exception--'
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
            u=sys.argv[0]+"?url="+urllib.quote_plus(vid_id)+"&mode=2&name="+urllib.quote_plus(name)
            liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
            liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": duration, "Plot": desc})
            liz.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=20)

        try:
            page_num = re.findall('next_page = (.+?);', data)[0]
            page = '?page='+page_num
            if not 'more' in url:
                url = url.replace('videos','more/videos')
            url = url.split('?page')[0]+page
            addDir(__language__(30031), url, 1, xbmc.translatePath(os.path.join(home, 'resources', 'next.png')))
        except:
            print '--- nextpage exception ---'


def playVid(url):
        url = 'http://vo.fod4.com/v/%s/v600.mp4' %url
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


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


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
    print ""
    get_categories()

elif mode==1:
    print ""+url
    index(url)

elif mode==2:
    print ""
    playVid(url)

xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))