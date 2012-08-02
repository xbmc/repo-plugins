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

__settings__ = xbmcaddon.Addon(id='plugin.video.twit')
__language__ = __settings__.getLocalizedString
playback = __settings__.getSetting('playback')
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join(home, 'fanart.jpg'))
icon = xbmc.translatePath( os.path.join(home, 'icon.png'))
cache = StorageServer.StorageServer("twit", 24)

thumbs = {
          'All About Android' : 'http://leo.am/podcasts/coverart/aaa600video.jpg',
          'Before You Buy' : 'http://leoville.tv/podcasts/coverart/byb600video.jpg',
          'FLOSS Weekly' : 'http://leoville.tv/podcasts/coverart/floss600video.jpg',
          'Frame Rate' : 'http://leoville.tv/podcasts/coverart/fr600video.jpg',
          'Ham Nation' : 'http://leoville.tv/podcasts/coverart/hn144video.jpg',
          'Home Theater Geeks' : 'http://leoville.tv/podcasts/coverart/htg144video.jpg',
          'iFive for the iPhone' : 'http://feeds.twit.tv/podcasts/coverart/ifive600video.jpg',
          'iPad Today' : 'http://leoville.tv/podcasts/coverart/ipad600video.jpg',
          'Know How...' : 'http://feeds.twit.tv/podcasts/coverart/kh600video.jpg',
          'MacBreak Weekly' : 'http://leoville.tv/podcasts/coverart/mbw144video.jpg',
          'NSFW' : 'http://leoville.tv/podcasts/coverart/nsfw144video.jpg',
          'Radio Leo' : 'http://twit.tv/files/imagecache/coverart-small/coverart/aaa600.jpg',
          'Security Now' : 'http://leoville.tv/podcasts/coverart/sn600video.jpg',
          'Tech News Today' : 'http://leoville.tv/podcasts/coverart/tnt144video.jpg',
          'The Giz Wiz' : 'http://static.mediafly.com/publisher/images/72acf86f350b40c5b5fd132dcacc78be/icon-600x600.png',
          'The Social Hour' : 'http://leoville.tv/podcasts/coverart/tsh600video.jpg',
          'The Tech Guy' : 'http://leoville.tv/podcasts/coverart/ttg144video.jpg',
          'This Week In Computer Hardware' : 'http://static.mediafly.com/publisher/images/f76d60fdd2ea4822adbc50d2027839ce/icon-600x600.png',
          'This Week in Enterprise Tech' : 'http://feeds.twit.tv/podcasts/coverart/twiet600video.jpg',
          'This Week in Google' : 'http://leoville.tv/podcasts/coverart/twig600video.jpg',
          'this WEEK in LAW' : 'http://static.mediafly.com/publisher/images/b2911bcc34174461ba970d2e38507340/icon-600x600.png',
          'this WEEK in TECH' : 'http://leoville.tv/podcasts/coverart/twit144video.jpg',
          'Triangulation' : 'http://static.mediafly.com/publisher/images/c60ef74e0a3545e490d7cefbc369d168/icon-600x600.png',
          'TWiT Live Specials' : 'http://leoville.tv/podcasts/coverart/specials144video.jpg',
          'Windows Weekly' : 'http://leoville.tv/podcasts/coverart/ww600video.jpg',
          }


def make_request(url):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://twit.tv'}
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


def get_thumb(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'class' : "dropdown"})[1]('option')
        for i in items:
            if i.string == 'RSS':
                feed_url = i['value']
                break
        try:
            thumb = re.compile('<itunes:image href="(.+?)"/>').findall(make_request(feed_url))[0].split(' ')[0].strip()
        except:
            try:
                thumb = soup('span', attrs={'class' : "field-content"})[0].img['src']
            except:
                thumb = icon
        return thumb


def show_check():
        try:
            show_list = json.loads(cache.get("show_list"))
        except:
            show_list = []
        url = 'http://twit.tv/shows'
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows = soup.findAll('div', attrs={'class' : 'item-list'})[2]('li')
        for i in shows:
            name = str(i('a')[-1].string)
            if not name in show_list:
                cache_shows(shows)
                break
        return(json.loads(cache.get("show_list")))


def cache_shows(shows):
        show_list = []
        for i in shows:
            name = str(i('a')[-1].string)
            url = ('http://twit.tv/show/'+name.replace("'",'').replace('.','').replace(' ','-').lower()
                   .replace('-for-the','').replace('the-giz-wiz','weekly-daily-giz-wiz'))
            try:
                thumb = thumbs[name]
            except:
                print '--- NO Thumb in Thumbs ---'
                try:
                    thumb = get_thumb(url)
                except:
                    thumb = icon
                    print '--- get_thumb FAILED: %s - %s ---' %(name, url)
            show_list.append((name, url, thumb))
        cache.set("show_list", json.dumps(show_list))


def get_shows():
        addDir(__language__(30038),'none',7,xbmc.translatePath(os.path.join(home, 'icon.png')))
        addDir(__language__(30000),'addLiveLinks',3,xbmc.translatePath(os.path.join(home, 'resources', 'live.png')))
        shows = cache.cacheFunction(show_check)
        for i in shows:
            if i[0] == 'Radio Leo': continue
            addDir(i[0], i[1], 1, i[2])


def index(url,iconimage):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.findAll('div', attrs={'id' : "primary"})[0]('div', attrs={'class' : 'field-content'})
        for i in items:
            url = i.a['href']
            if url.startswith('http://twit.tv/show/'):
                name = i.a.string.encode('ascii', 'ignore')
                try:
                    description = i.p.string
                except:
                    description = ''
                try:
                    date = i.findPrevious('span').string
                except:
                    date = ''
                addLink(name,url,description,date,2,iconimage)
        try:
            page = 'http://twit.tv'+soup('li', attrs={'class' : "pager-next"})[0].a['href']
            addDir('Next Page',page,1,iconimage)
        except:
            pass


def indexTwitFeed():
        url ='http://twit.tv/node/feed'
        soup = BeautifulStoneSoup(make_request(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        for i in soup('item'):
            try:
                title = i.title.string
                url = i.link
                date = i.pubdate.string.rsplit(' ', 1)[0]
                item_str = str(i).replace('  ','').replace('\n','')
            except:
                continue
            url_list = []
            try:
                vid_url_high = re.compile('HD Video URL:&nbsp;</div>(.+?)</div>').findall(item_str)[0]
            except:
                vid_url_high = 'no_url'
            url_list.append(vid_url_high)
            try:
                vid_url = re.compile('Video URL:&nbsp;</div>(.+?)</div>').findall(item_str)[0]
            except:
                vid_url = 'no_url'
            url_list.append(vid_url)
            try:
                vid_url_low = re.compile('Video URL \(mobile\):&nbsp;</div>(.+?)</div></div>').findall(item_str)[0]
            except:
                vid_url_low = 'no_url'
            url_list.append(vid_url_low)
            try:
                aud_url = re.compile('MP3 feed URL:&nbsp;</div>(.+?)</div></div></div>').findall(item_str)[0]
            except:
                aud_url = 'no_url'
            url_list.append(aud_url)

            url = setUrl(url_list, False)
            if not url == 'no_url':
                try:
                    episode_name = re.compile('<div class="field-item odd">(.+?)</div></div>').findall(item_str)[0]
                    if episode_name.startswith('<img'):
                        episode_name = re.compile('<div class="field-item odd"><p>(.+?)</p><p>').findall(item_str)[0]
                    episode_name = episode_name.replace('&amp;', '&').replace('&quot;', '"').replace('&#039;', "'").encode('ascii', 'ignore')
                except:
                    episode_name = ''
                try:
                    thumb = re.compile('<img src="(.+?)" alt=').findall(item_str)[0]
                except:
                    thumb = ''
                try:
                    desc = re.compile('<div class="field-item odd"><p>(.+?)</p></div></div>').findall(item_str)[0]
                    pattern = re.compile('<.+?>').findall(desc)
                    for i in pattern:
                        desc = desc.replace(i,'')
                    description = desc.replace('&amp;', '&').replace('&quot;', '"').replace('&#039;', "'")
                except:
                    description = ''
                name = title+' - '+episode_name
                addLink(name, url, description, date, 4, thumb)
            else: print '--- There was a problem adding episode %s ---' % title


def getVideo(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        url_list = ['no_url', 'no_url', 'no_url', 'no_url']
        for i in soup('span', attrs={'class' : "download"}):
            name = i.a['class']
            url = i.a['href']
            if name == 'audio download':
                url_list[3] = url
            if name == 'sd-low download':
                url_list[2] = url
            if name == 'sd download':
                url_list[1] = url
            if name == 'hd download':
                url_list[0] = url
        setUrl(url_list)


def setUrl(url_list, set=True):
        if playback == '3':
            url = url_list[3]
        if playback == '2':
            url = url_list[2]
            if url == 'no_url':
                url = url_list[1]
        if playback == '1':
            url = url_list[1]
            if url == 'no_url':
                url = url_list[2]
        if playback == '0':
            url = url_list[0]
            if url == 'no_url':
                url = url_list[1]
                if url == 'no_url':
                    url = url_list[2]
        if not set:
            return url
        else:
            if url == 'no_url':
                dialog = xbmcgui.Dialog()
                ret = dialog.yesno(__language__(30040), __language__(30039))
                if ret:
                    url = url_list[3]
                else: return
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def addLiveLinks():
        addLink(__language__(30032),'http://bglive-a.bitgravity.com/twit/live/high?noprefix','','',4,xbmc.translatePath( os.path.join( home, 'resources', 'live.png' ) ))
        addLink(__language__(30033),'http://bglive-a.bitgravity.com/twit/live/low?noprefix','','',4,xbmc.translatePath( os.path.join( home, 'resources', 'live.png' ) ))
        addLink(__language__(30034),'http://cgw.ustream.tv/Viewer/getStream/1/1524.amf','','',5,xbmc.translatePath( os.path.join( home, 'resources', 'live.png' ) ))
        addLink(__language__(30035),'URL','','',6,xbmc.translatePath( os.path.join( home, 'resources/live.png' ) ))
        addLink(__language__(30041),'http://twit.am/listen','','',4,xbmc.translatePath( os.path.join( home, 'resources', 'live.png' ) ))


def getUstream(url):
        def getSwf():
                url = 'http://www.ustream.tv/flash/viewer.swf'
                req = urllib2.Request(url)
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl
        data = make_request(url)
        match = re.compile('.*(rtmp://.+?)\x00.*').findall(data)
        rtmp = match[0]
        sName = re.compile('.*streamName\W\W\W(.+?)[/]*\x00.*').findall(data)
        playpath = ' playpath='+sName[0]
        swf = ' swfUrl='+getSwf()
        pageUrl = ' pageUrl=http://live.twit.tv'
        url = rtmp + playpath + swf + pageUrl + ' swfVfy=1 live=true'
        playLive(url)


def getJtv():
        soup = BeautifulSoup(make_request('http://usher.justin.tv/find/twit.xml?type=live'))
        token = ' jtv='+soup.token.string.replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
        rtmp = soup.connect.string+'/'+soup.play.string
        Pageurl = ' Pageurl=http://www.justin.tv/twit'
        swf = ' swfUrl=http://www.justin.tv/widgets/live_embed_player.swf?channel=twit'
        url = rtmp+token+swf+Pageurl
        playLive(url)


def playLive(url):
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


def addLink(name,url,description,date,mode,iconimage):
        try:
            description += "\n \n Published: " + date
        except:
            pass
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":description } )
        liz.setProperty( "Fanart_Image", fanart )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
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
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    get_shows()

elif mode==1:
    print ""
    index(url,iconimage)

elif mode==2:
    print ""
    getVideo(url)

elif mode==3:
    print ""
    addLiveLinks()

elif mode==4:
    print ""
    playLive(url)

elif mode==5:
    print ""
    getUstream(url)

elif mode==6:
    print ""
    getJtv()

elif mode==7:
    print ""
    indexTwitFeed()

elif mode==8:
    print ""
    setUrl(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))