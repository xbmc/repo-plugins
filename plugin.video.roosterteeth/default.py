import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
try:
    import json
except:
    import simplejson as json
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

cache = StorageServer.StorageServer("roosterteeth", 24)
addon = xbmcaddon.Addon(id='plugin.video.roosterteeth')
home = addon.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
base = 'http://roosterteeth.com'
language = addon.getLocalizedString


def make_request(url, location=False):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) Gecko/20100101 Firefox/12.0',
                       'Referer' : 'http://roosterteeth.com'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            response_url = urllib.unquote_plus(response.geturl())
            data = response.read()
            response.close()
            if location:
                return response_url
            else:
                return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification(%s,%s %s,5000,%s)"
                                    %(language(30000), language(30001), str(e.code), icon))


def cache_shows():
        rt_url = 'http://roosterteeth.com/archive/series.php'
        ah_url = 'http://ah.roosterteeth.com/archive/series.php'
        soup = BeautifulSoup(make_request(rt_url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        ah_soup = BeautifulSoup(make_request(ah_url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows = []
        items = soup('table', attrs={'class' : "border boxBorder"})[0].table('tr')
        items += ah_soup('table', attrs={'class' : "border boxBorder"})[0].table('tr')
        items += soup('table', attrs={'class' : "border boxBorder"})[1].table('tr')
        items += ah_soup('table', attrs={'class' : "border boxBorder"})[1].table('tr')
        for i in items:
            try:
                show = (i.b.string, i.a['href'], i.img['src'])
                if not show in shows:
                    shows.append(show)
            except: continue
        return(str(shows))


def get_shows():
        shows = eval(cache.cacheFunction(cache_shows))
        for i in shows:
            if 'v=trending' in i[1]:
                i[1] = i[1].replace('v=trending','v=more')
            addDir(i[0], base+i[1], 1, i[2])


def get_seasons(url,iconimage):
        try:
            soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
            items = soup('td', attrs={'class' : "seasonsBox"})[0]('a')
            for i in items:
                print i['href']
                addDir(i.string, base+i['href'], 2, iconimage, True)
        except IndexError:
            index(url, False)


def index(url, season=True):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        if season:
            items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[1]('a')
        else:
            items = soup('div', attrs={'id' : "profileAjaxContent"})[0]('table')[0]('a')
        for i in items:
            href = i['href']
            item_id = href.split('id=')[1].split('&')[0]
            try:
                thumb = i.img['src']
            except:
                thumb = icon
            name = i('span')[0].string
            if name is None:
                name = i('span')[0].contents[0]
            try:
                if (not i('span')[1].string is None) and (not i('span')[1].string in name):
                    name += ': '+ i('span')[1].string
            except:
                pass
            duration = i.td.string
            if duration is None:
                diration = ''
            addLink(name, item_id, thumb, duration, 3)
        try:
            next_page = soup('a', attrs={'id' : "streamLoadMore"})[0]['href']
            addDir(language(30002), base+next_page, 2, xbmc.translatePath(os.path.join(home, 'resources', 'next.png')), season)
        except:
            print "Didn't find next page!"


def resolve_url(item_id):
        url = 'http://roosterteeth.com/archive/new/_loadEpisode.php?id=%s&v=morev' %item_id
        data = json.loads(make_request(url))
        soup = BeautifulSoup(data['embed']['html'], convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            filetype = soup.div['data-filetype']
            if filetype == 'youtube':
                youtube_id = soup.iframe['src'].split('/')[-1].split('?')[0]
                print ' youtube id: '+youtube_id
                path = 'plugin://plugin.video.youtube/?action=play_video&videoid='+youtube_id
            elif filetype == 'blip':
                blip_url = soup.iframe['src']
                print 'blip_url: '+blip_url
                path = get_blip_location(blip_url)
        except:
            sorry = "Sorry, you must be a Sponsor to see this video."
            if sorry in str(soup):
                    xbmc.executebuiltin("XBMC.Notification(%s,%s,5000,%s)" 
                                        %(language(30000), language(30003), icon))
                    print sorry
                    return
            else:
                print '-- Unknown Error: here is the soup --'
                print soup
                return
        item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def get_blip_location(blip_url):
        blip_url = make_request(blip_url, True)
        pattern = re.compile('http://blip.tv/rss/flash/(.+?)&')
        blip_xml = 'http://blip.tv/rss/flash/'+pattern.findall(blip_url)[0]
        url = None
        soup = BeautifulStoneSoup(make_request(blip_xml), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        if addon.getSetting('quality') == '0':
            try:
                url = soup('media:content', attrs={'blip:role' : 'Blip HD 720'})[0]['url']
            except:
                try:
                    url = soup('media:content', attrs={'blip:role' : 'Source'})[0]['url']
                except:
                    pass
                    
        elif addon.getSetting('quality') == '1':
            try:
                url = soup('media:content', attrs={'blip:role' : 'Blip SD'})[0]['url']
            except:
                try:
                    url = soup('media:content', attrs={'blip:role' : 'Blip LD'})[0]['url']
                except:
                    try:
                        url = soup('media:content', attrs={'blip:role' : 'web'})[0]['url']
                    except:
                        try:
                            url = soup('media:content', attrs={'blip:role' : 'Portable (iPod)'})[0]['url']
                        except:
                            pass
                            
        if (url is None) or (addon.getSetting('quality') == '2'):
            try:
                url = soup('media:content', attrs={'isdefault' : 'true'})[0]['url']
            except:
                try:
                    url = soup.enclosure['url']
                except:
                     print ' -- URL was not found --'
                     return
        return url


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


def addLink(name,url,iconimage,duration,mode):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration })
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage,season=False):
        u=(sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        +"&season="+str(season)+"&iconimage="+urllib.quote_plus(iconimage))
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
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
    season=eval(params["season"])
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
    get_shows()

elif mode==1:
    get_seasons(url,iconimage)

elif mode==2:
    index(url, season)

elif mode==3:
    resolve_url(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))