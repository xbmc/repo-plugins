import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json
import StorageServer

cache = StorageServer.StorageServer("techcrunch", 1)
addon = xbmcaddon.Addon(id='plugin.video.techcrunch')
home = addon.getAddonInfo('path')
debug = addon.getSetting('debug')
addon_version = addon.getAddonInfo('version')
icon = os.path.join(home, 'icon.png')
if debug == 'true':
    cache.dbg = True


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.techcrunch-%s]: %s" %(addon_version, string))


def make_request(url):
        addon_log('Request URL: ' + url)
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0',
                       'Referer' : 'http://techcrunch.com/'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            addon_log('ResponseInfo: %s' %response.info())
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: ', e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)


def cache_shows():
        url = 'http://techcrunch.com/video/'
        soup = BeautifulSoup(make_request('http://techcrunch.com/video/'), convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows = []
        for i in soup.findAll('div', attrs={'class': "show-shadow"}):
            show=i.fetchPrevious('a')[0]
            videos = []
            show_panel = soup.find('div', attrs={'id': show['id'].replace('list','panel')})
            items = show_panel.findAllNext('a', attrs={'class': 'video'})[:8]
            for item in items:
                href = item['href']
                title = item.find('span', attrs={'class': 'video-excerpt-title'}).string
                date = item.find('p', attrs={'class': 'video-post-date'}).string
                thumb = item.img['src'].split('?')[0]
                videos.append((title, href, date, thumb))

            try:
                page = show_panel.findNext('div', attrs={'class': 'load-more-results'})
                page_info ={}
                page_info['title'] = page.a.string
                page_info['offset'] = page.a['data-offset']
                page_info['showid'] = page.a['data-showid']
                page_info['total'] = page.a['data-totalvideos']
            except:
                page_info = None
            if show.string == 'All Videos':
                show.string = 'Most Recent'
            shows.append({'name': show.string, 'id': show['id'], 'videos': videos, 'page_info': page_info})
        return shows


def get_shows():
        shows = cache.cacheFunction(cache_shows)
        for i in shows:
            addDir(i['name'], i['id'], 1, icon)


def get_show(name, url):
        shows = cache.cacheFunction(cache_shows)
        for i in shows:
            if i['name'] == name:
                videos = i['videos']
                page_info = i['page_info']
                break
            else: continue
        for i in videos:
            addDir(i[0].encode('utf-8'), i[1], 2,  i[3], i[2], True)

        ## can't figure this one out??, seems* we need to send cookies that are generated via javascript.
        # if page_info:
            # page_url = ('http://techcrunch.com/wp-admin/admin-ajax.php?action=tc_load_more_videos&show_id=%s&offset=%s'
                        # %(page_info['showid'], page_info['offset']))
            # addDir(page_info['title'], page_url, 3, os.path.join(home, 'resources', 'next.png'))


def load_more_videos(url, name):
        pass


def resolve_url(url):
        video_url = ''
        success = False
        quality = {'0': '_2.mp4', '1': '_64.webm'}
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        script = soup.find('div', attrs={'class': 'body-copy'}).script['src']
        p = script.split('&')[1:]
        params={}
        for i in p:
            if not i == '':
                params[i.split('=')[0]] = i.split('=')[1]
        json_url=('http://syn.5min.com/handlers/SenseHandler.ashx?func=GetResults&sid=577'
                  '&isPlayerSeed=true&playlist='+params['playList']+'&videoCount=50&autoStart=false'
                  '&cbCustomID=fiveMinCB_1&videoGroupID='+params['videoGroupID']+'&url='+urllib.quote(url))
        data = json.loads(make_request(json_url))
        if data['success']:
            for i in data['binding']:
                if str(i['ID']) == params['playList']:
                    embed_url = i['EmbededURL']
                    break
        else:
            addon_log('No json data')
        try:
            video_url = urllib.unquote(re.findall('videoUrl=(.+?)&', embed_url)[0].replace('.mp4', quality[addon.getSetting('quality')]))
            success = True
        except:
            addon_log('Exception: Video URL')
        item = xbmcgui.ListItem(path=video_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


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


def addDir(name,url,mode,iconimage,date='',isplayable=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": date } )
        isfolder=True
        if isplayable:
            liz.setProperty('IsPlayable', 'true')
            isfolder=False
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
    mode=int(params["mode"])
except:
    pass

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    get_shows()

if mode==1:
    get_show(name, url)

if mode==2:
    resolve_url(url)

if mode==3:
    load_more_videos(url, name)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
