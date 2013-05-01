import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import StorageServer
from datetime import datetime
from pyamf import remoting
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
try:
    import json
except:
    import simplejson as json

addon = xbmcaddon.Addon(id='plugin.video.twit')
__language__ = addon.getLocalizedString
addon_version = addon.getAddonInfo('version')
home = xbmc.translatePath(addon.getAddonInfo('path'))
fanart = os.path.join(home, 'fanart.jpg')
icon = os.path.join(home, 'icon.png')
live_icon = 'http://twit-xbmc.googlecode.com/svn/images/live_icon.png'
cache = StorageServer.StorageServer("twit", 2)
debug = addon.getSetting('debug')
first_run = addon.getSetting('first_run')


def addon_log(string):
        if debug == 'true':
            xbmc.log("[addon.TWiT-%s]: %s" %(addon_version, string))


def cache_shows_file():
        show_file = os.path.join(home, 'resources', 'shows')
        cache.set("shows", open(show_file, 'r').read())


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
            addon_log( 'We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: ', e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)


def shows_cache(shows):
        url = 'http://twit.tv/shows'
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        show_items = soup.findAll('div', attrs={'class' : 'item-list'})[2]('li')
        for i in show_items:
            name = str(i('a')[-1].string)
            try:
                show = shows[name]
            except:
                addon_log('Show not in cache: '+name)
                show_url = ('http://twit.tv/show/'+name.replace("'",'').replace('.','').replace(' ','-').lower()
                            .replace('-for-the','').replace('the-giz-wiz','weekly-daily-giz-wiz'))
                new_show = cache_show(name, show_url)
                if new_show:
                    addon_log('Cached new show: '+name)
        return "True"


def cache_show(name, url):
        shows = eval(cache.get('shows'))
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            desc = soup.find('div', attrs={'class': "field-content"}).getText()
            if desc == None: raise
        except:
            addon_log('description exception: '+name)
            desc = ''
        try:
            thumb = soup.find('div', attrs={'class' : "views-field views-field-field-cover-art-fid"})('img')['src']
            if thumb == None: raise
        except:
            addon_log('thumb exception: '+name)
            thumb = icon
        shows[name] = {'show_url': url, 'thumb': thumb, 'description': desc}
        cache.set("shows", repr(shows))
        return True


def get_shows(shows):
        addDir(__language__(30000),'latest_episodes',4,icon)
        addLink(__language__(30001),'twit_live','','',3,live_icon)
        cache_shows = eval(cache.cacheFunction(shows_cache, shows))
        if not cache_shows:
            addon_log('shows_cache FAILED')
        items = sorted(shows.keys(), key=str.lower)
        for i in items:
            if i == 'Radio Leo': continue
            addDir(i, shows[i]['show_url'], 1, shows[i]['thumb'], shows[i]['description'])


def index(url,iconimage):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.findAll('div', attrs={'id' : "primary"})[0]('div', attrs={'class' : 'field-content'})
        for i in items:
            try:
                url = i.a['href']
            except TypeError:
                continue
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


def cache_latest_episods():
        shows = eval(cache.get('shows'))
        url = 'http://twit.tv/'
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        h_tag = soup.find('h2', attrs={'class': 'block-title'}, text='Most Recent Episodes')
        items_string = str(h_tag.findNext('div', attrs={'class': "view-content"})('div'))
        items_string = items_string.replace('\n','').replace('> <','><').replace('>, <','><')
        pattern = (
            '<span class="field-content">(.+?)</span></div><div class=".+?"><span class=".+?">'
            '<div class="coverart"><img src="(.+?)" alt="" title="" width=".+?" height=".+?" class=".+?" />'
            '</div><div class="show-info"><a href="(.+?)">(.+?)</a>(.+?) </div></span></div><div class=".+?">'
            '<div class="field-content"><p>(.+?)</p>'
            )
        items_list = re.findall(pattern, items_string)
        episode_list = []
        episodes = ''
        for show, thumb, href, episode, date, desc in items_list:
            if episode in episodes:
                addon_log('episode already in list')
                continue
            name = '%s - %s' %(show, episode)
            try:
                thumbnail = shows[show]['thumb']
            except:
                addon_log('thumbnail exception: '+show)
                thumbnail = thumb
            episode_list.append((name,href,desc,date,thumbnail))
            episodes += episode+', '
        return episode_list


def get_latest_episodes():
        episodes = cache.cacheFunction(cache_latest_episods)
        for i in episodes:
            addLink(i[0], i[1], i[2], i[3], 2, i[4])


def set_media_url(url):
        playback_settings = {
            '0': 'hd download',
            '1': 'sd download',
            '2': 'download',
            '3': 'audio download'
            }
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        media_urls = {}
        for i in soup('span', attrs={'class' : "download"}):
            media_urls[i.a['class']] = i.a['href']
        if content_type == 'audio':
            playback_setting = '3'
            playback_type = 'audio download'
        else:
            playback_setting = addon.getSetting('playback')
            playback_type = playback_settings[playback_setting]
        playback_url = None
        if media_urls.has_key(playback_type):
            playback_url = media_urls[playback_type]
        else:
            p_set = int(playback_setting)
            if (p_set + 1) <= 3:
                for i in range(len(playback_settings)):
                    p_set += 1
                    if p_set < 3:
                        try:
                            playback_url = media_urls[playback_settings[str(p_set)]]
                            break
                        except: continue
        if not playback_url:
            dialog = xbmcgui.Dialog()
            ret = dialog.select(__language__(30002), media_urls.keys())
            playback_url = media_urls.values()[ret]

        if playback_url:
            success = True
        else:
            success = False
            playback_url = ''
        item = xbmcgui.ListItem(path=playback_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def twit_live():
        live_streams = [
            'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/high/playlist.m3u8',
            'http://twit.live-s.cdn.bitgravity.com/cdn-live-s1/_definst_/twit/live/low/playlist.m3u8',
            'http://bglive-a.bitgravity.com/twit/live/high?noprefix',
            'http://bglive-a.bitgravity.com/twit/live/low?noprefix',
            'ustream',
            'justintv',
            'http://hls.twit.tv:1935/flosoft/_definst_/mp4:twitStreamHi_1628/playlist.m3u8',
            'http://hls.twit.tv:1935/flosoft/_definst_/mp4:twitStream_1128/playlist.m3u8',
            'http://hls.twit.tv:1935/flosoft/_definst_/mp4:twitStream_696/playlist.m3u8',
            'http://hls.twit.tv:1935/flosoft/_definst_/mp4:twitStream_496/playlist.m3u8',
            'http://twit.am/listen'
            ]
        if content_type == 'audio':
            link = 'http://twit.am/listen'
        else:
            link = live_streams[int(addon.getSetting('twit_live'))]
            if link == 'justintv':
                link = get_jtv()
            elif link == 'ustream':
                link = get_ustream()
        success = False
        if link:
            success = True
        else: link = ''
        item = xbmcgui.ListItem(path=link)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def get_ustream():
        def getSwf():
                url = 'http://www.ustream.tv/flash/viewer.swf'
                req = urllib2.Request(url)
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl
        data = make_request('http://cgw.ustream.tv/Viewer/getStream/1/1524.amf')
        amf_data = remoting.decode(data).bodies[0][1].body
        if amf_data['success']:
            hls_url = None
            if amf_data.has_key('liveHttpUrl'):
                try: hls_url = amf_data['liveHttpUrl']
                except: pass
            if hls_url:
                return hls_url
            else:
                streams = None
                try:
                    streams = amf_data['streamVersions']['streams/live_1']['streamVersionCdn']
                except: pass
                if streams:
                    for i in streams.keys():
                        rtmp = streams[i].values()[0]
                        path = streams[i].values()[1]
                        break
                    playpath = ' playpath='+path
                    swf = ' swfUrl='+getSwf()
                    pageUrl = ' pageUrl=http://live.twit.tv'
                    url = rtmp + playpath + swf + pageUrl + ' swfVfy=1 live=true'
                    return url
                else:
                    return None


def get_jtv():
        try:
            soup = BeautifulSoup(make_request('http://usher.justin.tv/find/twit.xml?type=live'))
            token = ' jtv='+soup.token.string.replace('\\','\\5c').replace(' ','\\20').replace('"','\\22')
            rtmp = soup.connect.string+'/'+soup.play.string
            Pageurl = ' Pageurl=http://www.justin.tv/twit'
            swf = ' swfUrl=http://www.justin.tv/widgets/live_embed_player.swf?channel=twit live=true'
            url = rtmp+token+swf+Pageurl
            return url
        except:
            return None


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
        u=(sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+
           "&iconimage="+urllib.quote_plus(iconimage)+"&content_type="+content_type)
        ok=True
        episode = None
        try: episode = int(re.findall('#(.+?):', name)[0])
        except:
            try: episode = int(name.split(' ')[-1])
            except: pass
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"Title": name, "Plot":description, "Aired": date, "episode": episode})
        liz.setProperty("Fanart_Image", fanart)
        liz.setProperty('IsPlayable', 'true')
        if name == __language__(30001):
            contextMenu = [('Run IrcChat', "RunPlugin(plugin://plugin.video.twit/?mode=5)")]
            liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage,description=None):
        u=(sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+
           "&iconimage="+urllib.quote_plus(iconimage)+"&content_type="+content_type)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"Title": name, "Plot":description})
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


def run_ircchat():
        # check_chat_args
        nickname = addon.getSetting('nickname')
        username = addon.getSetting('username')
        try:
            ok = nickname
            if ok is None or ok == '': raise
            ok = username
            if ok is None or ok == '': raise
        except:
            xbmc.executebuiltin("XBMC.Notification(%s, %s,10000,%s)"
                %('IrcChat', language(30024), icon))
            addon.openSettings()
            nickname = addon.getSetting('nickname')
            username = addon.getSetting('username')
            try:
                ok = nickname
                if ok is None or ok == '': raise
                ok = username
                if ok is None or ok == '': raise
            except:
                return
        # run ircchat script
        xbmc.executebuiltin(
            "RunScript(script.ircchat, run_irc=True&nickname=%s&username=%s&password=%s&host=irc.twit.tv&channel=twitlive)"
            %(nickname, username, addon.getSetting('password'))
            )


def setViewMode():
        if not addon.getSetting('view_mode') == "0":
            try:
                if addon.getSetting('view_mode') == "1": # List
                    xbmc.executebuiltin('Container.SetViewMode(502)')
                elif addon.getSetting('view_mode') == "2": # Big List
                    xbmc.executebuiltin('Container.SetViewMode(51)')
                elif addon.getSetting('view_mode') == "3": # Thumbnails
                    xbmc.executebuiltin('Container.SetViewMode(500)')
                elif addon.getSetting('view_mode') == "4": # Poster Wrap
                    xbmc.executebuiltin('Container.SetViewMode(501)')
                elif addon.getSetting('view_mode') == "5": # Fanart
                    xbmc.executebuiltin('Container.SetViewMode(508)')
                elif addon.getSetting('view_mode') == "6":  # Media info
                    xbmc.executebuiltin('Container.SetViewMode(504)')
                elif addon.getSetting('view_mode') == "7": # Media info 2
                    xbmc.executebuiltin('Container.SetViewMode(503)')
                elif addon.getSetting('view_mode') == "8": # Media info 3
                    xbmc.executebuiltin('Container.SetViewMode(515)')
            except:
                addon_log("SetViewMode Failed: "+addon.getSetting('view_mode'))
                addon_log("Skin: "+xbmc.getSkinDir())


if debug == 'true':
    cache.dbg = True

if first_run != addon_version:
    cache_shows_file()
    addon_log('first_run, caching shows file')
    xbmc.sleep(1000)
    addon.setSetting('first_run', addon_version)

params=get_params()
url=None
name=None
mode=None
content_type='video'

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
try:
    content_type=str(params["content_type"])
except:
    pass

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    try:
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            get_shows(shows)
        else: raise
    except:
        addon_log('"shows" cache missing')
        cache_shows_file()
        addon_log('caching shows file, this should only happen if common cache db is reset')
        xbmc.sleep(1000)
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            get_shows(shows)
        else:
            addon_log('"shows" cache ERROR')
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==1:
    index(url,iconimage)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    setViewMode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==2:
    set_media_url(url)

elif mode==3:
    twit_live()
    xbmc.sleep(1000)
    if addon.getSetting('run_chat') == 'true':
        run_ircchat()

elif mode==4:
    get_latest_episodes()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode==5:
    run_ircchat()
