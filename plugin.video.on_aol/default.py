# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json
import StorageServer

base_url = 'http://on.aol.com'
cache = StorageServer.StorageServer("onaol", 1)
addon = xbmcaddon.Addon(id='plugin.video.on_aol')
home = xbmc.translatePath(addon.getAddonInfo('path'))
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
debug = addon.getSetting('debug')
addon_version = addon.getAddonInfo('version')
icon = os.path.join(home, 'icon.png')
fanart = os.path.join(home, 'fanart.jpg')
fav_png = os.path.join(home, 'resources', 'fav.png')
next_png = os.path.join(home, 'resources', 'next.png')
search_png = os.path.join(home, 'resources', 'search.png')
search_file = os.path.join(profile, 'search_queries')
fav_file = os.path.join(profile, 'favorites')
__language__ = addon.getLocalizedString

if addon.getSetting('save_search') == 'true':
    save_search = True
else:
    save_search = False
try:
    favorites = eval(open(fav_file, 'r').read())
except:
    favorites = []

if debug == 'true':
    cache.dbg = True


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.on_aol-%s]: %s" %(addon_version, string))


def make_request(url):
        addon_log('Request URL: ' + url)
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0',
                       'Referer' : base_url}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            addon_log('ResponseInfo: %s' %response.info())
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' %url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' %e.code)


def get_page_items(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        channels = []
        if url == base_url:
            for i in soup.noscript('a'):
                channels.append((i.string, i['href']))

        partners = []
        try:
            for i in soup('div', attrs={'class': "featured-studios-items clearfix"})[0]('a'):
                partners.append((i['title'], i['href'], i.find('img')['src']))
        except IndexError: pass

        top_picks = []
        items = soup('div', attrs={'class': "related-thumbs related-full"})[0]('div', attrs={'class': 'thumb-image'})
        for i in items:
            top_picks.append((i.img['alt'], i.a['href'], i.img['src']))

        featured = []
        try:
            for i in soup('div', attrs={'class': 'slider_container'})[0]('div', attrs={'class': "slide"}):
                featured.append((i.a['title'], i.a['href'], i.img['src']))
        except IndexError: pass

        more_topics = []
        try:
            if soup.find('div', attrs={'class': 'column'})('h2', text='MORE TOPICS'):
                for i in soup.find('div', attrs={'class':"horizontal-paging-container"})('a'):
                        more_topics.append((i.string, i['href']))
        except: pass

        addon_log('channels: %s, partners: %s, top_picks: %s, featured: %s, more_topics: %s'
                  %(len(channels), len(partners), len(top_picks), len(featured), len(more_topics)))
        return {
            'channels': channels,
            'partners': partners,
            'top_picks': top_picks,
            'featured': featured,
            'more_topics': more_topics
            }


def cache_topics():
        soup = BeautifulSoup(make_request(base_url+'/topics/all'), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'class': "topic-category-item"})
        topics = []
        for i in items:
            icon = i.img['src']
            topic_items=[]
            for c in i('a'):
                href = c['href']
                title = c.string
                if title is None:
                    categorie = href.split('/')[-1].replace('-',' ').title()
                else:
                    topic_items.append((title, href))
            topics.append({'title': categorie, 'items': topic_items, 'icon': icon})
        return topics


def cache_home_page():
        return get_page_items(base_url)


def get_home_page(url=None):
        if url is None:
            items = cache.cacheFunction(cache_home_page)
        else:
            items = get_page_items(url)
        cache.set("current_items", repr(items))
        for i in items.keys():
            addon_log('%s: %s' %(i, len(items[i])))
            if len(items[i]) > 0:
                title = None
                if i == 'featured':
                    title = __language__(30000)
                elif i == 'top_picks':
                    title = __language__(30001)
                elif i == 'partners':
                        title = __language__(30002)
                if title:
                    addDir(title, i, 7, icon)
        for i in items.keys():
            if len(items[i]) > 0:
                if url is None:
                    if i == 'channels':
                        addDir(__language__(30003), i, 7, icon)
                elif i == 'more_topics':
                    for t in items[i]:
                        addDir(t[0], t[1], 2, icon)
        if url is None:
            addDir(__language__(30004), '', 5, icon)
            addDir(__language__(30005), '', 13, search_png)
            addDir(__language__(30020), '', 10, fav_png)


def get_home_page_item(item):
        items = eval(cache.get("current_items"))[item]
        for i in items:
            addon_log('%s: %s' %(item, i))
            if (item == 'featured') or (item == 'top_picks'):
                addDir(i[0].encode('utf-8'), i[1], 3, i[2], True, '', '', True)
            elif item == 'channels':
                if not i[0] == 'Homepage':
                    if not i[0] == 'More Topics':
                        addDir(i[0], i[1], 6, icon, True)
            elif item == 'partners':
                addDir(i[0], i[1], 2, i[2], True)


def get_topics():
        for i in cache.cacheFunction(cache_topics):
            addDir(i['title'], '', 1, i['icon'], True)


def get_topic(name):
        topics = cache.cacheFunction(cache_topics)
        for i in topics:
            if i['title'] == name:
                for item in i['items']:
                    addDir(item[0], item[1], 2, i['icon'], True)
                break
            else: continue


def get_videos(url):
        if not url.startswith(base_url):
            url = base_url+url
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        try: items = soup.find('div', attrs={'class': "search-results topics-results"})('div', attrs={'class': 'thumb'})
        except TypeError:
            try: items = soup.find('div', attrs={'class': "videos_container"})('div', attrs={'class': 'thumb'})
            except:
                addon_log('No items found')
                return
        for i in items:
            href = i.a['href']
            title = i.a['title'].encode('utf-8')
            thumb = i.img['src']
            date = i.find('span', attrs={'class': 'date'}).string
            desc = i.find('span', attrs={'class': 'description'}).string
            addDir(title, href, 3, thumb, True, date, desc, True)
        for i in soup.findAll('a', attrs={'class': "page"}):
            if i.string.encode('utf-8') == '›':
                if not i['href'].split('/')[-1] == '1':
                    if not i['href'] == url:
                        addDir(__language__(30007), i['href'], 2, next_png)


def resolve_url(url):
        if not url.startswith(base_url):
            url = base_url+url
        video_url = ''
        success = False
        quality = {
            '0': ['_16.webm','_128.mp4', '_1.mp4'],
            '1': ['_32.webm', '_2.mp4'],
            '2': ['_64.webm', '_4.mp4'],
            '3': [ '_8.mp4']
            }
        playlist_id = re.split('-|=', url)[-1]
        json_url = (
            'http://syn.5min.com/handlers/SenseHandler.ashx?func=GetResults&sid=577&isPlayerSeed=true&playlist='+playlist_id+
            '&videoCount=1&autoStart=true&cbCustomID=fiveMinCB_videos_companion&relatedMode=0&videoControlDisplayColor=3355443'
            '&colorPallet=16777215&ExposureType=PlayerSeed&hasCompanion=true&url='+urllib.quote(url)+'&filterString=&cbCount=3'
            '&cbHtmlID=fiveMinCB_videos_companion_cb&cbWidth=300&cbHeight=60&cbHtmlID1=fiveMinCB_videos_companion_fb&cbWidth1=300'
            '&cbHeight1=137&cbIsFairBalance1=true&cbHtmlID2=fiveMinCB_videos_companion_bt'
            )
        data = json.loads(make_request(json_url))
        if data['success']:
            for i in data['binding']:
                if str(i['ID']) == playlist_id:
                    embed_url = i['EmbededURL']
                    quality_types=[]
                    for t in i['Renditions']:
                        quality_types.append('_%s.%s' %(t['ID'],t['RenditionType']))
                    addon_log('Renditions: %s' %i['Renditions'])
                    addon_log('Quality Types: %s' %quality_types)
                    break
        else:
            addon_log('No json data')
        extension = None
        for i in quality[addon.getSetting('quality')]:
            addon_log('looking for %s in %s' %(i, quality_types))
            if i in quality_types:
                extension = i
        if not extension:
            quality_set = int(addon.getSetting('quality'))
            if quality_set > 0:
                for i in range(quality_set):
                    if quality_set > 0:
                        addon_log('Quality Setting Not Available: %s' %quality_set)
                        quality_set = (quality_set - 1)
                        for e in quality[str(quality_set)]:
                            addon_log('looking for %s in %s' %(e, quality_types))
                            if e in quality_types:
                                extension = e
                                break
                    if extension:
                        break

        if not extension:
            addon_log('Unknown Extension: %s' %quality_types)
            extension = quality_types[0]
        addon_log('Using video url extension: %s' %extension)
        try:
            video_url = urllib.unquote(re.findall('videoUrl=(.+?)&', embed_url)[0].replace('.mp4', extension))
            success = True
        except:
            addon_log('Exception: Video URL')
        item = xbmcgui.ListItem(path=video_url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def search(search_url):
        if not search_url.startswith(base_url):
            keyboard = xbmc.Keyboard('', __language__(30006))
            keyboard.doModal()
            if keyboard.isConfirmed() == False:
                return
            search_query = keyboard.getText()
            if len(search_query) == 0:
                return
            search_url = ('http://on.aol.com/ajax/search/GetSearchPageResults/%s/%s/1/relevance/'
                          %(urllib.quote(search_query), search_url))
            if save_search:
                add_search(search_query, search_url)

        data = json.loads(make_request(search_url))
        partner = False
        if 'Partners' in search_url:
            key = 'Partners'
            partner = True
        else: key = 'Videos'
        total = data[key]['Total']
        page = data[key]['Page']
        items = data[key]['Results']
        for i in items:
            if partner:
                addDir(i['DisplayName'], i['Link'], 2, i['Thumbnail'], True, i['CreatedOn'], i['Description'])
            else:
                addDir(i['Title'], i['Link'], 3, i['Thumbnail'], True, i['PubDate'], i['Description'], True)
        if (page * 10) < total:
            addDir(__language__(30007), search_url.replace(('/%s/' %page), ('/%s/' %(page+1))), 8, next_png)


def get_search():
        addDir(__language__(30015), 'Videos', 8, search_png)
        addDir(__language__(30016), 'Partners', 8, search_png)
        if save_search:
            if xbmcvfs.exists(search_file):
                items = eval(open(search_file, 'r').read())
                for i in items:
                    addDir(i[0], i[1], 8, search_png, 'search')


def add_search(search_query, search_url):
        if xbmcvfs.exists(search_file):
            search_list = eval(open(search_file, 'r').read())
        else: search_list = []
        search_list.append((search_query, search_url))
        add = open(search_file, 'w')
        add.write(repr(search_list))
        add.close()


def rm_search(search_query):
        search_list = eval(open(search_file, 'r').read())
        for i in range(len(search_list)):
            if search_query == search_list[i][0]:
                del search_list[i]
                break
        rm = open(search_file, 'w')
        rm.write(repr(search_list))
        rm.close()
        xbmc.executebuiltin("XBMC.Container.Refresh")


def get_fav():
        for i in favorites:
            addDir(i[0], i[1], i[2], i[3], 'fav', i[4], i[5], eval(i[6]))


def add_fav(name, url, fav_mode, thumb, date, desc, isplayable):
        favorites.append((name, url, fav_mode, thumb, date, desc, isplayable))
        add = open(fav_file, 'w')
        add.write(repr(favorites))
        add.close()


def rm_fav(name):
        for i in range(len(favorites)):
            if name == favorites[i][0]:
                del favorites[i]
                break
        rm = open(fav_file, 'w')
        rm.write(repr(favorites))
        rm.close()
        xbmc.executebuiltin("XBMC.Container.Refresh")


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


def addDir(name,url,mode,iconimage,menu=False,date='', desc='',isplayable=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc+'\n'+date})
        liz.setProperty("Fanart_Image", fanart)
        isfolder=True
        if isplayable:
            liz.setProperty('IsPlayable', 'true')
            isfolder=False
        if menu:
            contextMenu = []
            if menu == 'search':
                if save_search:
                    contextMenu.append((__language__(30017),'XBMC.RunPlugin(%s?mode=9&name=%s)'
                                        %(sys.argv[0], urllib.quote_plus(name))))
            elif menu == 'fav':
                for i in favorites:
                    if i[0] == name:
                        contextMenu.append((__language__(30018), 'XBMC.RunPlugin(%s?mode=12&name=%s)'
                                            %(sys.argv[0], urllib.quote_plus(name))))
            else:
                contextMenu.append((
                    __language__(30019),
                    'XBMC.RunPlugin(%s?url=%s&mode=11&name=%s&thumb=%s&isplayable=%s&fav_mode=%s&date=%s&desc=%s)'
                    %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name), urllib.quote_plus(iconimage),
                    repr(isplayable), str(mode), urllib.quote_plus(date), urllib.quote_plus(desc.encode('utf-8')))
                    ))
            liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isfolder)
        return ok


params=get_params()
url=None
name=None
mode=None
thumb=None
isplayable=None
fav_mode=None
date=None
desc=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    thumb=urllib.unquote_plus(params["thumb"])
except:
    pass
try:
    date=urllib.unquote_plus(params["date"])
except:
    pass
try:
    desc=urllib.unquote_plus(params["desc"])
except:
    pass
try:
    isplayable=(params["isplayable"])
except:
    pass
try:
    fav_mode=int(params["fav_mode"])
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
    get_home_page()

if mode==1:
    get_topic(name)

if mode==2:
    get_videos(url)

if mode==3:
    resolve_url(url)

if mode==4:
    get_page_items(url)

if mode==5:
    get_topics()

if mode==6:
    get_home_page(url)

if mode==7:
    get_home_page_item(url)

if mode==8:
    search(url)

if mode==9:
    rm_search(name)

if mode==10:
    get_fav()

if mode==11:
    add_fav(name, url, fav_mode, thumb, date, desc, isplayable)

if mode==12:
    rm_fav(name)

if mode==13:
    get_search()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
