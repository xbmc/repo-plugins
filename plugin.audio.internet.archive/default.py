import urllib
import urllib2
import re
import os
import ast
import xbmcplugin
import xbmcgui
import xbmcaddon
import SimpleDownloader as downloader
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.internet.archive')
__language__ = __settings__.getLocalizedString
home = xbmc.translatePath(__settings__.getAddonInfo('path'))
icon = os.path.join(home, 'icon.png')
fanart = os.path.join(home, 'fanart.jpg')
sort = __settings__.getSetting('sort_by')
base_url = 'http://www.archive.org'
downloader = downloader.SimpleDownloader()
debug = __settings__.getSetting('debug')
addon_version = __settings__.getAddonInfo('version')

if sort=="":
    sort = __language__(30011)
    set = 'downloads'
elif sort==__language__(30009):
    set = 'publicdate'
elif sort==__language__(30010):
    set = 'date'
elif sort==__language__(30011):
    set = 'downloads'
elif sort==__language__(30012):
    set = 'avg_rating%3B-num_reviews'


def addon_log(string):
        if debug == 'true':
            xbmc.log("[addon.internet.archive-%s]: %s" %(addon_version, string))


def getResponse(url):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            link = response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: ', e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' % e.code)
                xbmc.executebuiltin("XBMC.Notification("+__language__(30000)+","+__language__(30001)+str(e.code)+",5000,"+icon+")")


def getCategories(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        if 'etree' in url:
            thumb = 'http://ia600202.us.archive.org/17/items/etree/lma.jpg'
        else:
            thumb = iconimage
        try:
            try:
                spotlight_url = soup('div', attrs={'id' : "spotlight"})[0]('a')[1]['href']
            except:
                try:
                    spotlight_url = soup('div', attrs={'id' : "spotlight"})[0]('a')[0]['href']
                except:
                    addon_log('spotlight_url not found')
                    raise
            try:
                spotlight_name = soup('div', attrs={'id' : "spotlight"})[0]('a')[1].string.encode('utf-8')
            except:
                try:
                    spotlight_name = soup('div', attrs={'id' : "spotlight"})[0]('a')[0].string.encode('utf-8')
                except:
                    spotlight_name = 'Unknown'
            try:
                spotlight_thumb = soup('div', attrs={'id' : "spotlight"})[0].img['src']
            except:
                spotlight_thumb = thumb
            try:
                spotlight_desc = soup('div', attrs={'id' : "spotlight"})[0].br.next.string.encode('utf-8')
            except:
                spotlight_desc = 'no desc'
            addDir(coloring( 'Spotlight Item',"cyan",'Spotlight Item' )+' - '+spotlight_name,
                   base_url+spotlight_url, 3, spotlight_desc, spotlight_thumb.split('?')[0])
        except:
            pass

        items = soup('div', attrs={'id' : "description"})[0]('a')
        for i in items:
            name = i.string
            if name == 'All items (most recently added first)':
                addDir(name,base_url+i['href'],2,'',thumb)
                name = name.replace('most recently added first','By Addon Setting: '+sort)
                href = i['href'].replace('publicdate',set)
                addDir(name,base_url+href,2,'',thumb)
            if name == 'Browse Collection':
                addDir(name+' by average rating / number of reviews',base_url+i['href'],2,'',thumb)
            if name == 'Browse by Subject / Keywords':
                addDir(name,base_url+i['href'],7,'',thumb)
            if name == 'Browse by Language':
                addDir(name,base_url+i['href'],8,'',thumb)
            if name == 'Browse All Artists with Recordings in the Live Music Archive':
                addDir(name,i['href'],11,'',thumb)
            if name == 'Grateful Dead':
                addDir(name,i['href'],1,'',thumb)
        if soup('div', attrs={'id' : "browseauthor"}):
            addDir(__language__(30002),url,4,'',thumb)
        if soup('div', attrs={'id' : "browsetitle"}):
            addDir(__language__(30003),url,5,'',thumb)
        addDir(__language__(30004),url.split('/')[-1],6,'',thumb)
        try:
            categories = soup('div', attrs={'id' : 'subcollections'})[0]('tr')
            for i in categories:
                if len(i.nobr.string) > 1:
                    try:
                        name = i('a')[1].string.encode('utf-8')
                    except:
                        try:
                            name = i('a')[0].string.encode('utf-8')
                        except:
                            name = 'Unknown'
                    url = base_url+i.a['href']
                    try:
                        thumb = base_url+i.img['src']
                    except:
                        pass
                    desc = i.br.next.encode('utf-8', 'ignore')
                    addDir(name+' ('+i.nobr.string+')',url,1,desc,thumb)
                else:
                    addon_log('No Categories')
        except:
            addon_log('exception: categories')


def getShowList(url, iconimage):
        if 'gutenberg' in url:
            href = url.split('sort=')[0]+'3%20AND%20mediatype%3Aaudio'
            if set in url:
                url = href+'sort=-'+set
            else:
                url = href
        link = getResponse(url)
        try:
            soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        except:
            addon_log('SOUP ERROR')
            soup = BeautifulSoup(link)
        try:
            items = soup('table', attrs={'class' : "resultsTable"})[0]('tr')
        except IndexError:
            pattern = re.compile('<b>Search engine returned invalid information or was unresponsive</b>')
            if pattern.search(link):
                xbmc.executebuiltin("XBMC.Notification("+__language__(30000)+","+__language__(30020)+",10000,"+icon+")")
            return
        for i in items:
            try:
                href = i.a['href']
            except:
                addon_log('No URL')
                continue
            try:
                if len(i.a.contents)>1:
                    name_list=[]
                    for n in i.a.contents:
                        names = n.string
                        name_list.append(names)
                    try:
                        name = "".join(name_list)
                    except:
                        name = name_list[0]
                else:
                    try:
                        name = i('a')[0].string
                    except:
                        raise
            except:
                name = 'Unknown'

            desc = ''
            try:
                desc = i.br.next
            except:
                addon_log('exception: description')
            if desc != '':
                try:
                    if 'class="searchTerm"' in str(desc):
                        desc = i.span.next.next
                    if 'Keywords:</span>' in str(desc):
                        raise
                except:
                    desc = ''
            try:
                addDir(name,base_url+href,3,desc,iconimage)
            except:
                try:
                    addon_log("exception: trying ('utf-8', 'ignore')")
                    desc = desc.encode('utf-8', 'ignore')
                    addDir(name.encode('utf-8', 'ignore'),base_url+href,3,desc,iconimage)
                except:
                    try:
                        addDir(name.encode('utf-8', 'ignore'),base_url+href,3,'',iconimage)
                        addon_log('DESC ERROR: Name: '+name.encode('utf-8', 'ignore'))
                    except:
                        addon_log('There was an error adding show Directory')
                        try:
                            addon_log('NAME: '+name)
                        except:
                            addon_log('NAME ERROR')
                        try:
                            addon_log('URL: '+href)
                        except:
                            addon_log('URL ERROR')
        try:
            page = re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)[0]
            url = base_url+page.replace('&amp;','&')
            addDir(__language__(30007),url,2,'',iconimage)
        except:
            addon_log('exception: next page')
            pass


def getMedia(url, title, iconimage):
        link = getResponse(url)
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            dl_items = soup('div', attrs={'id' : 'col1'})[0]('a')
            if dl_items > 0:
                downloads = get_media_downloads(dl_items)
            else:
                downloads = None
                addon_log('No Downloads')
        except:
            addon_log('error getting downloads')
            downloads = None
        thumb = None
        try:
            for i in range(len(soup.findAll('td', attrs={'class' : "ttlHeader"}))):
                if soup.findAll('td', attrs={'class' : "ttlHeader"})[i].string == 'Image Files':
                    a = soup.findAll('td', attrs={'class' : "ttlHeader"})[i]
                    thumb = a.findNext('a')['href']
        except: pass
        if not thumb:
            try:
                thumb = soup('div', attrs={'id' : 'col1'})[0].img['src']
                if thumb == '/images/glogo.png?cnt=0':
                    thumb = None
                    raise
            except: pass
        if not thumb:
            try:
                thumb = base_url+soup('table', attrs={'id' : "ff4"})[0]('a')[0]['href']
                if not thumb.find('.jpg' or '.gif'):
                    thumb = base_url+soup('table', attrs={'id' : "ff4"})[0]('a')[1]['href']
                    if not thumb.find('.jpg' or '.gif'):
                        thumb = None
                        raise
            except: pass
        if not thumb:
            try:
                thumb = re.compile('<a href=".+?"><img title=".+?" alt=".+?" id=".+?" src="(.+?)?cnt=0"/></a>').findall(link)[0]
            except:
                try:
                    thumb = re.compile('<img id="thumbnail" src="(.+?)" style=".+?" alt=".+?" title=".+?">').findall(link)[0]
                except:
                    thumb = iconimage
        try:
            duration = re.findall('Run time: (.+?)\n', str(soup('div', attrs={'id' : 'col1'})[0]))[0].split('  ')[0]
            if 'minutes' in duration:
                duration = duration.split(' minutes')[0]+':00'
        except:
            duration = ''
        scripts = soup('script')
        data = False
        for i in scripts:
            if "Play('jw6'," in str(i):
                try:
                    pattern = re.compile('Play\(\'jw6\',\[(.+?)\],{"start"')
                    data = ast.literal_eval(pattern.findall(str([i]).replace('\n','').replace('  ',''))[0])
                except:
                    addon_log('execption: data')
                break
        if data:
            if isinstance(data, dict):
                data = [data]
            m_type = None
            href = None
            for i in data:
                try:
                    duration = i['duration']
                except KeyError: pass
                duration = str(duration).split('.')[0]
                name = i['title']
                try:
                    thumb = i['image']
                except KeyError: pass
                for m in i['sources']:
                    if m['type'] == 'mp3':
                        href = m['file']
                    elif m['type'] == 'video/h264':
                        href = m['file']
                if href is None:
                    href = i['sources'][0]['file']
                if thumb.startswith('/'):
                    thumb = base_url+thumb
                if href.endswith('mp3' or 'ogg' or 'flac'):
                    m_type = 'audio'
                    desc = title
                else:
                    try:
                        desc = ''
                        d = soup('div', attrs={'id' : "midcol"})[0]('p', attrs={'class' : 'content'})[0].contents
                        for i in range(len(d)):
                            if str(d[i]) != '<br />':
                                desc += str(d[i]).split('<')[0]
                    except:
                        addon_log('exception: description')
                        desc = title
                addLink(name, base_url+href, desc, duration, thumb, m_type, downloads)
        else:
            if downloads is not None:
                list_downloads(str(downloads), thumb)


def get_media_downloads(items):
        dl_types = ['VBR M3U', 'Torrent', 'VBR ZIP', 'h.264', 'h.264 720P', 'DivX', 'HTTPS',
                    'QuickTime', 'Ogg Video', 'CD/DVD', 'MPEG1', 'MPEG4', '512Kb MPEG4',
                    'HiRes MPEG4', 'MPEG2', '64Kb MPEG4', '256Kb MPEG4', 'Cinepack', 'Windows Media']
        downloads = []
        for i in items:
            name = i.string
            url = None
            if name in dl_types:
                if name == 'CD/DVD':
                    name = 'CD-DVD ISO'
                if name == 'HTTPS':
                    name = 'All Files'
                if name == 'Torrent':
                    name += ' File'
                if not 'File' in name:
                    try:
                        if (i.findPrevious('span').string is None) or (i.findPrevious('span').string == 'NEW!'):
                            pass
                        else:
                            name += ' ' + i.findPrevious('span').string
                    except:
                        addon_log('get size of %s exception' %name)
                href = i['href']
                if href.startswith('http'):
                    url = href
                else:
                    url = base_url+href
                downloads.append((str(name), str(url)))
            else: continue
        return downloads


def get_all_files(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)('a')
        for i in soup:
            if not i.string.endswith('/'):
                dl_url = url+'/'+i['href']
                u=sys.argv[0]+"?url="+urllib.quote_plus(dl_url)+"&mode=9"
                liz=xbmcgui.ListItem(i.string, iconImage=iconimage, thumbnailImage=iconimage)
                liz.setProperty("Fanart_Image", fanart)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)


def getBrowseKeyword(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('tbody')[3]('li')
        for i in items:
            try:
                name = i.a.string.encode('utf-8')
                href = i.a['href']
                addDir(name,base_url+href,2,'',iconimage)
            except:
                addon_log('There was an error adding Directory')


def getBrowseByTitle(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browsetitle"})[0]('a')
        addon_log('Items: %s' %len(items))
        for i in items:
            try:
                name = i.string.encode('utf-8')
                href = i['href'].replace(' ','%20')
                addDir(name,base_url+href,2,'',iconimage)
            except:
                addon_log('There was an error adding Directory')


def getBrowseByAuthor(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browseauthor"})[0]('a')
        for i in items:
            try:
                name = i.string.encode('utf-8')
                href = i['href'].replace(' ','%20')
                addDir(name,base_url+href,2,'',iconimage)
            except:
                addon_log('There was an error adding Directory')


def getBrowseLanguage(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('table', attrs={'id' : "browse"})[0]('a')
        for i in items:
            name = i.string.encode('utf-8')
            items = i.next.next[:-1].encode('utf-8')
            href = i['href']
            addDir(name+items,base_url+href,2,'',iconimage)


def getBrowseByArtist(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('table', attrs={'id' : "browse"})[0]('li')
        for i in items:
            name = i('a')[0].string.encode('utf-8')
            shows = i('a')[1].string.encode('utf-8')
            href = i.a['href']
            addDir(name+' ( '+shows+' )',base_url+href,1,'',iconimage)


def Search(url, iconimage):
        searchStr = ''
        keyboard = xbmc.Keyboard(searchStr, "Search")
        keyboard.doModal()
        if (keyboard.isConfirmed() == False):
            return
        searchstring = keyboard.getText()
        newStr = searchstring.replace(' ','%20')
        if len(newStr) == 0:
            return
        url = 'http://www.archive.org/search.php?query='+newStr+'%20AND%20collection%3A'+url+'&sort=-'+set
        getShowList(url, iconimage)


def DownloadFiles(url):
        path = __settings__.getSetting('download')
        if path == "":
            xbmc.executebuiltin("XBMC.Notification("+__language__(30000)+","+__language__(30015)+",10000,"+icon+")")
            __settings__.openSettings()
        path = __settings__.getSetting('download')
        if path == "":
            return
        name = url.rsplit('/', 1)[1]
        params = {"url": url, "download_path": path, "Title": name}
        addon_log('######### Download #############')
        addon_log(str(params))
        addon_log('################################')
        downloader.download(name, params)


def list_downloads(downloads, iconimage):
        downloads = ast.literal_eval(downloads)
        for i in downloads:
            try:
                if (i[0] == 'All Files') or (i[0] == 'all files'):
                    name = 'List All Files For Download'
                    mode = '12'
                    url = i[1]
                    isfolder = True
                else:
                    mode = '9'
                    url = base_url+i[1]
                    isfolder = False
                    name = 'Download - %s' %i[0]
                u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode+"&iconimage="+urllib.quote_plus(iconimage)
                liz=xbmcgui.ListItem(coloring(name ,"cyan", name), iconImage=iconimage, thumbnailImage=iconimage)
                liz.setProperty("Fanart_Image", fanart)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isfolder)
            except: pass


 # Thanks to gifty for the coloring function!
def coloring( text , color , colorword ):
        if color == "white":
            color="FFFFFFFF"
        if color == "blue":
            color="FF0000FF"
        if color == "cyan":
            color="FF00B7EB"
        if color == "violet":
            color="FFEE82EE"
        if color == "pink":
            color="FFFF1493"
        if color == "red":
            color="FFFF0000"
        if color == "green":
            color="FF00FF00"
        if color == "yellow":
            color="FFFFFF00"
        if color == "orange":
            color="FFFF4500"
        colored_text = text.replace( colorword , "[COLOR=%s]%s[/COLOR]" % ( color , colorword ) )
        return colored_text


def getInHMS(seconds):
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    if hours == 0:
        return "%02d:%02d" % (minutes, seconds)
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


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


def addLink(name, url, desc, duration, iconimage, m_type, downloads):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        tracknumber = ''
        if '. ' in name:
            tracknumber = int(name.split('. ')[0])
            name = name.split('. ')[1]
        if m_type is 'audio':
            name = name.replace('>',' ')
            if ' Live at ' in desc:
                artist = desc.split(' Live at ')[0]
                album = 'Live At '+desc.split(' Live at ')[1]
            elif ' - ' in desc:
                artist = desc.split(' - ')[0]
                album = desc.split(' - ')[1]
            else:
                artist = ''
                album = ''
            try:
                year = int(re.findall(' on (.+?)-.+?-.+?', desc)[0])
            except:
                year = ''
            liz.setInfo(type="Music", infoLabels={"Title": name, "Duration": int(duration), "Album": album,
                                                  "Artist": artist, "Tracknumber": tracknumber, "Year": year})
        else:
            if duration != '':
                if not ':' in duration:
                    duration = getInHMS(int(duration))
            liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration,
                                                  "Tracknumber": tracknumber})
        contextMenu = []
        try:
            dl_name = name
            extension = url.rsplit('.', 1)[1]
            dl_name += '.'
            dl_name += extension
        except:
            dl_name = url.rsplit('/', 1)[1]
        contextMenu.append((('Download - %s' %dl_name, 'XBMC.RunPlugin(%s?url=%s&mode=9)'
                             %(sys.argv[0], urllib.quote_plus(url)))))
        if downloads is not None:
            if len(downloads) < 8:
                for i in downloads:
                        if i[0] == 'All Files':
                            contextMenu.append(('List %s For Download' %i[0],'XBMC.Container.Update(%s?url=%s&mode=12&iconimage=%s)'
                                                %(sys.argv[0], urllib.quote_plus(i[1]), urllib.quote_plus(iconimage))))
                        else:
                            contextMenu.append(('Download - %s' %i[0],'XBMC.RunPlugin(%s?url=%s&mode=9)'
                                                %(sys.argv[0], urllib.quote_plus(i[1]))))
            else:
                contextMenu.append(('Get Download List (%s)' %str(len(downloads)),'XBMC.Container.Update(%s?mode=10&downloads=%s&iconimage=%s)'
                                    %(sys.argv[0], str(downloads).replace(', ','__'), urllib.quote_plus(iconimage))))
        liz.addContextMenuItems(contextMenu)
        liz.setProperty("Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok


def addDir(name, url, mode, desc, iconimage):
        u=(sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+
           "&desc="+urllib.quote_plus(desc)+"&iconimage="+urllib.quote_plus(iconimage))
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        liz.setProperty("Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


params=get_params()
url=None
name=None
mode=None
iconimage=None
desc=None
content_type=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    desc=urllib.unquote_plus(params["desc"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    downloads=params["downloads"].replace('__',', ')
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    content_type=params["content_type"]
except:
    pass

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    if content_type == 'audio':
        getCategories('http://www.archive.org/details/audio', 'http://ia600304.us.archive.org/25/items/audio/audio.gif')
    elif content_type == 'video':
        getCategories('http://www.archive.org/details/movies', 'http://ia700303.us.archive.org/0/items/movies/movies.gif')
    else:
        addDir(__language__(30016),'http://www.archive.org/details/audio',1,'','http://ia600304.us.archive.org/25/items/audio/audio.gif')
        addDir(__language__(30017),'http://www.archive.org/details/movies',1,'','http://ia700303.us.archive.org/0/items/movies/movies.gif')

elif mode==1:
    addon_log("getCategories")
    getCategories(url, iconimage)

elif mode==2:
    addon_log("getShowList")
    getShowList(url, iconimage)

elif mode==3:
    addon_log("getMedia")
    getMedia(url, name, iconimage)

elif mode==4:
    addon_log("getBrowseByAuthor")
    getBrowseByAuthor(url, iconimage)

elif mode==5:
    addon_log("getBrowseByTitle")
    getBrowseByTitle(url, iconimage)

elif mode==6:
    addon_log("Search")
    Search(url, iconimage)

elif mode==7:
    addon_log("getBrowseKeyword")
    getBrowseKeyword(url, iconimage)

elif mode==8:
    addon_log("getBrowseLanguage")
    getBrowseLanguage(url, iconimage)

elif mode==9:
    addon_log("DownloadFiles")
    DownloadFiles(url)

elif mode==10:
    addon_log("list_downloads")
    list_downloads(downloads, iconimage)

elif mode==11:
    addon_log("getBrowseByArtist")
    getBrowseByArtist(url, iconimage)

elif mode==12:
    addon_log("get_all_files")
    get_all_files(url, iconimage)

xbmcplugin.endOfDirectory(int(sys.argv[1]))