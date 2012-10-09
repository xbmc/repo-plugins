import urllib
import urllib2
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import StorageServer
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.video.fox.news')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
cache = StorageServer.StorageServer("foxnews", 24)
quality = __settings__.getSetting('quality')


def make_request(url, headers=None):
        if headers is None:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
                       'Referer' : 'http://video.foxnews.com'}
        try:
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


def get_categories():
        url = 'http://video.foxnews.com/playlist/latest-featured-videos/'
        data = make_request(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        add_dir(soup.body.h1.contents[0].strip(), '', 2, icon)
        h = soup.find('div', attrs={'class' : 'all'})
        for i in h.findNext('ul')('a'):
            add_dir(i.string, i['href'], 1, icon)
        cache.set("videos_dict", repr({ "videos": get_video_list(data) }))


def get_sub_categories(url):
        if url.startswith('/?'):
            url = 'http://video.foxnews.com'+url
        elif url.startswith('//video.foxnews'):
            url = 'http:'+url
        data = make_request(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        featured_name = soup.body.h1.contents[0].strip()
        add_dir(featured_name, '', 2, icon)
        items = soup('div', attrs={'id' : 'shows'})[0]('a')
        for i in items:
            name = i.string
            if name != featured_name:
                href = 'http:'+i['href']
                add_dir(name, href, 3, icon)
        cache.set("videos_dict", repr({ "videos": get_video_list(data) }))


def get_video_list(html, url=None):
        if url is None:
            soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        else:
            soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.find('div', attrs={'class' : 'pl'})('li')
        video_list = []
        for i in items:
            href = i.a['href']
            name = i.h2.a.string
            thumb = i.img['src']
            date = i.time.string
            duration = i.strong.string
            desc = i.span.string
            if url is not None:
                add_link(date, name, duration, href, thumb, desc)
            else:
                video_list.append((date, name, duration, href, thumb, desc))
        if url is None:
            return video_list


def get_featured_videos():
        for i in eval(cache.get("videos_dict"))['videos']:
            add_link(i[0], i[1], i[2], i[3], i[4], i[5])


def get_json_data(video_id):
        url = 'http://video.foxnews.com/v/feed/video/%s.js?' %video_id
        data = json.loads(make_request(url))
        try:
            video_url = data['channel']['item']['media-content']['@attributes']['url']
            if video_url is None: raise
            else: return video_url
        except:
            try:
                video_url = data['channel']['item']['media-content']['mvn-fnc_mp4']
                if video_url is None: raise
                else: return video_url
            except:
                try:
                    video_url = data['channel']['item']['media-content']['mvn-flv1200']
                    if video_url is None: raise
                    else: return video_url
                except:
                    print '-- No video_url --'
                    return None


def get_smil(video_id):
        smil_url = 'http://video.foxnews.com/v/feed/video/%s.smil' %video_id
        headers = {'Referer' : 'http://video.foxnews.com/assets/akamai/FoxNewsPlayer.swf',
                   'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
        soup = BeautifulSoup(make_request(smil_url, headers))
        try:
            return soup.find('meta', attrs={'name' : "rtmpAuthBase"})['content'] + soup.find('video')['src']
        except: return None


def resolve_url(url):
        quality_types = {'0' : '_FNC_HIGH.',
                         '1' : '_FNC_MED.',
                         '2' : '_FNC_MED_LOW.',
                         '3' : '_FNC_LOW.'}
        quality_type = quality_types[quality]
        video_id = url.split('/v/')[1].split('/')[0]
        vidoe_url = None
        try:
            video_url = get_smil(video_id)
            if vidoe_url is None: raise
        except:
            try:
                video_url = get_json_data(video_id)
                if vidoe_url is None: raise
            except: pass
        if video_url is None:
            succeeded = False
            playback_url = ''
        else:
            succeeded = True
        if succeeded:
            if not quality_type in video_url:
                for i in quality_types.values():
                    if i in video_url:
                        playback_url = video_url.replace(i, quality_type)
                        break
            else: playback_url = video_url
        item = xbmcgui.ListItem(path=playback_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), succeeded, item)



def add_link(date, name, duration, href, thumb, desc):
        description = date+'\n\n'+desc
        u=sys.argv[0]+"?url="+urllib.quote_plus(href)+"&mode=4"
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
        liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Duration": duration})
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)



def add_dir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


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


xbmcplugin.setContent(int(sys.argv[1]), 'movies')

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

if mode==None:
    get_categories()

elif mode==1:
    get_sub_categories(url)

elif mode==2:
    get_featured_videos()

elif mode==3:
    get_video_list(None, url)

elif mode==4:
    resolve_url(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))