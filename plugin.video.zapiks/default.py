import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.zapiks')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_method')
home = __settings__.getAddonInfo('path')
base = 'http://www.zapiks.com'
icon_path = 'http://zapiks-xbmc.googlecode.com/svn/images/'
fanart = icon_path+'fanart.jpg'

def getRequest(url):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
                   'Referer' : base}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data


def categories():
        soup = BeautifulSoup(getRequest(base), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('ul', attrs={'id' : "sports_navigation"})[0]('a')
        for i in items:
            href = i['href']
            if not href == '#':
                href = i['href'][:-1]
                if sort == '0':
                    href = href+'1'
                if sort == '1':
                    href = href+'/popular_1.php'
                if sort == '2':
                    href = href+'/alltimebuzzed_1.php'
                if sort == '3':
                    href = '/_'+href[1:]+'/premium_1.php'
                title = i.string
                thumb = icon_path+i.string+'.png'
                addDir(title, base+href, 1, thumb)
        addDir(__language__(30000), 'getPartners', 3, icon_path+'partner.png')


def getPartners():
        soup = BeautifulSoup(getRequest(base), convertEntities=BeautifulSoup.HTML_ENTITIES)
        partners_items = soup('div', attrs={'id' : "partners"})[0]('a')
        pro_items = soup('div', attrs={'id' : "pro_all"})[0]('a')
        for i in pro_items:
            items = partners_items.append(i)
        for i in partners_items:
            href = i['href']
            title = i['title']
            thumb = i.img['src']
            addDir(title, base+href, 1, thumb)


def indexPage(url):
        soup = BeautifulSoup(getRequest(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        videos = soup.findAll('div', attrs={'class' : "media_thumbnail medium"})
        for i in videos:
            try:
                url = i('a')[0]['href']
                name = i('a')[0]['title']
                thumb = i('img')[0]['src']
                addLink(name, base+url, 2, thumb)
            except:
                continue
        try:
            nextPage = soup.find('span', attrs={'class' : "next"})('a')[1]['href']
            addDir(__language__(30001), base+nextPage, 1, os.path.join(home, 'resources', 'images', 'next.png'))
        except:
            pass


def videoLinks(url):
        soup = BeautifulSoup(getRequest(url))
        vid = soup.find('link', attrs={'rel' : "video_src"})['href']
        new_soup = BeautifulSoup(getRequest('http://www.zapiks.com/view/index.php?file='+vid[-5:]+'&lang=fr'))
        item = xbmcgui.ListItem(path = new_soup.file.string)
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


def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty("IsPlayable","true")
        liz.setProperty("Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty("Fanart_Image", fanart)
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
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    categories()

elif mode==1:
    print ""
    indexPage(url)

elif mode==2:
    print ""
    videoLinks(url)

elif mode==3:
    print ""
    getPartners()

xbmcplugin.endOfDirectory(int(sys.argv[1]))