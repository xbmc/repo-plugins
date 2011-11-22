import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.internet.archive')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )
sort = __settings__.getSetting('sort_by')
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


def getResponse(url):
        try:
            req = urllib2.Request(url)
            req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
            response = urllib2.urlopen(req)
            link = response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification("+__language__(30000)+","+__language__(30001)+str(e.code)+",5000,"+icon+")")


def getCategories(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            thumb = soup('td', attrs={'style' : "width:80px; height:72px; vertical-align:middle; text-align:right"})[0].img['src']
            if thumb.startswith('/'):
                thumb = 'http://www.archive.org'+thumb
            if 'animationandcartoons/animation-header.gif' in thumb:
                thumb = iconimage
            if 'newsandpublicaffairs/news-header.gif' in thumb:
                thumb = iconimage
            if 'artsandmusicvideos/artsmusic-header.gif' in thumb:
                thumb = iconimage
            if 'vlogs/vlogs-header.gif' in thumb:
                thumb = iconimage
            if 'youth_media/flip-youthmedia-icon.gif' in thumb:
                thumb = iconimage
            if 'gamevideos/videogames-header.gif' in thumb:
                thumb = iconimage
            if 'ephemera/flip-ephemera-header.gif' in thumb:
                thumb = iconimage
        except:
            thumb = iconimage
        try:
            try:
                spotlight_url = soup('div', attrs={'id' : "spotlight"})[0]('a')[1]['href']
            except:
                try:
                    spotlight_url = soup('div', attrs={'id' : "spotlight"})[0]('a')[0]['href']
                except:
                    print '#spotlight_url not found#'
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
                spotlight_thumb = iconimage

            try:
                spotlight_desc = soup('div', attrs={'id' : "spotlight"})[0].br.next.string.encode('utf-8')
            except:
                spotlight_desc = 'no desc'

            addDir(coloring( 'Spotlight Item',"cyan",'Spotlight Item' )+' - '+spotlight_name, 'http://www.archive.org'+spotlight_url, 3, spotlight_desc, spotlight_thumb.split('?')[0])
        except:
            pass

        items = soup('div', attrs={'id' : "description"})[0]('a')
        for i in items:
            name = i.string
            if name == 'All items (most recently added first)':
                addDir(name,'http://www.archive.org'+i['href'],2,'',thumb)
                name = name.replace('most recently added first','By Addon Setting: '+sort)
                href = i['href'].replace('publicdate',set)
                addDir(name,'http://www.archive.org'+href,2,'',thumb)
            if name == 'Browse Collection':
                addDir(name+' by average rating / number of reviews','http://www.archive.org'+i['href'],2,'',thumb)
            if name == 'Browse by Subject / Keywords':
                addDir(name,'http://www.archive.org'+i['href'],7,'',thumb)
            if name == 'Browse by Language':
                addDir(name,'http://www.archive.org'+i['href'],8,'',thumb)
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
                    url = 'http://www.archive.org'+i.a['href']
                    try:
                        thumb = 'http://www.archive.org'+i.img['src']
                    except:
                        pass
                    desc = i.br.next.encode('utf-8', 'ignore')
                    addDir(name+' ('+i.nobr.string+')',url,1,desc,thumb)
        except:
            print 'No Categories'

	
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
            print 'SOUP ERROR'
            soup = BeautifulSoup(link)

        items = soup('table', attrs={'class' : "resultsTable"})[0]('tr')
        for i in items:
            try:
                href = i.a['href']
            except:
                print 'No URL'
                pass
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

            try:
                desc = i.br.next
            except:
                desc = ''
            try:
                if 'class="searchTerm"' in str(desc):
                    desc = i.span.next.next
                if 'Keywords:</span>' in str(desc):
                    desc = "No Description"
            except:
                desc = 'Description Error'
            try:
                addDir(name,'http://www.archive.org'+href,3,desc,iconimage)
            except:
                try:
                    desc = desc.encode('utf-8', 'ignore')
                except:
                    desc = 'Description Error 2'
                try:
                    addDir(name.encode('utf-8', 'ignore'),'http://www.archive.org'+href,3,desc,iconimage)
                except:
                    print 'There was an error adding show Directory'
                    try:
                        print 'NAME: '+name
                    except:
                        print 'NAME ERROR'
                        pass
                    try:
                        print 'URL: '+href
                    except:
                        print 'URL ERROR'
                        pass
                    try:
                        print 'DESC: '+desc
                    except:
                        print 'DESC ERROR'
                        pass

        try:
            page = re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)[0]
            url = 'http://www.archive.org'+page.replace('&amp;','&')
            addDir(__language__(30007),url,2,'',iconimage)
        except:
            pass


def getMedia(url, desc, iconimage):
        link = getResponse(url)
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)

        try:
            thumb = soup('div', attrs={'id' : "col1"})[0]('img')[0]['src']
            if thumb == '/images/glogo.png?cnt=0':
                raise
        except:
            try:
                thumb = 'http://www.archive.org'+soup('table', attrs={'id' : "ff4"})[0]('a')[0]['href']
                if not thumb.find('.jpg'):
                    if not thumb.find('.gif'):
                        thumb = 'http://www.archive.org'+soup('table', attrs={'id' : "ff4"})[0]('a')[1]['href']
                        if not thumb.find('.jpg'):
                            if not thumb.find('.gif'):
                                raise
            except:
                try:
                    thumb = re.compile('<a href=".+?"><img title=".+?" alt=".+?" id=".+?" src="(.+?)?cnt=0"/></a>').findall(link)[0]
                except:
                    try:
                        thumb = re.compile('<img id="thumbnail" src="(.+?)" style=".+?" alt=".+?" title=".+?">').findall(link)[0]
                    except:
                        thumb = iconimage
        if thumb.startswith('/'):
            thumb = 'http://www.archive.org'+thumb

        try:
            match = re.compile("IAD.mrss = '(.+?)'").findall(link)[0]
            soupRss = BeautifulStoneSoup(match, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
            if len(soupRss('item')) > 1:
                # add Play All listitem
                u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=10"+"&iconimage="+urllib.quote_plus(thumb)
                ok=True
                liz=xbmcgui.ListItem(coloring( __language__(30005), "cyan", __language__(30005)), iconImage=xbmc.translatePath(os.path.join(home, 'resources', 'play.png')), thumbnailImage=xbmc.translatePath(os.path.join(home, 'resources', 'play.png')))
                liz.setProperty( "Fanart_Image", fanart )
                ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)

            for i in soupRss('item'):
                name = urllib.unquote_plus(i('media:title')[0].string.encode("utf-8", 'ignore'))
                url = i ('media:content')[0]['url']
                try:
                    duration = i('media:content')[0]['duration']
                except:
                    duration = ''
                try:
                    img = 'http://www.archive.org'+i('media:thumbnail')[0]['url']
                    if img == 'http://www.archive.org/images/glogo.png':
                        raise
                except:
                    img = thumb
                addLink(name, 'http://www.archive.org'+url, desc, duration, img)
        except:
            pass

        try:
            items = soup('p', attrs={'id' : "dl"})[0]('a')
            for i in items:
                url = i['href']
                name = i.string
                size = i.findPrevious('span').string
                if 'NEW' in size:
                    size = ''
                addLink(coloring( __language__(30006),"orange",__language__(30006) )+name+' '+size, 'http://www.archive.org'+url, desc, '', thumb)
        except:
            pass


def getPlaylist(url, iconimage):
        player = xbmc.Player()
        if player.isPlaying():
            player.stop()
        playlist = xbmc.PlayList(0)
        playlist.clear()

        match = re.compile("IAD.mrss = '(.+?)'").findall(getResponse(url))[0]
        soup = BeautifulStoneSoup(match, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        for i in soup('item'):
            name = urllib.unquote_plus(i('media:title')[0].string.encode("utf-8"))
            url = i ('media:content')[0]['url']
            try:
                duration = i('media:content')[0]['duration']
            except:
                duration = ''
            liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
            liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration } )
            playlist.add(url='http://www.archive.org'+url, listitem=liz)
        xbmc.executebuiltin('playlist.playoffset(music,0)')


def getBrowseKeyword(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('tbody')[3]('li')
        for i in items:
            try:
                name = i.a.string.encode('utf-8')
                href = i.a['href']
                addDir(name,'http://www.archive.org'+href,2,'',iconimage)
            except:
                print 'There was an error adding Directory'


def getBrowseByTitle(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browsetitle"})[0]('a')
        print len(items)
        for i in items:
            try:
                name = i.string.encode('utf-8')
                href = i['href'].replace(' ','%20')
                addDir(name,'http://www.archive.org'+href,2,'',iconimage)
            except:
                print 'There was an error adding Directory'


def getBrowseByAuthor(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browseauthor"})[0]('a')
        for i in items:
            try:
                name = i.string.encode('utf-8')
                href = i['href'].replace(' ','%20')
                addDir(name,'http://www.archive.org'+href,2,'',iconimage)
            except:
                print 'There was an error adding Directory'


def getBrowseLanguage(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('table', attrs={'id' : "browse"})[0]('a')
        for i in items:
            name = i.string.encode('utf-8')
            items = i.next.next[:-1].encode('utf-8')
            href = i['href']
            addDir(name+items,'http://www.archive.org'+href,2,'',iconimage)


def getBrowseByArtist(url, iconimage):
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('table', attrs={'id' : "browse"})[0]('li')
        for i in items:
            name = i('a')[0].string.encode('utf-8')
            shows = i('a')[1].string.encode('utf-8')
            href = i.a['href']
            addDir(name+' ( '+shows+' )','http://www.archive.org'+href,1,'',iconimage)


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
        filename = url.split('/')[-1]
        def download(url, dest):
            dialog = xbmcgui.DialogProgress()
            dialog.create(__settings__.getLocalizedString(30000), __settings__.getLocalizedString(30013), filename)
            urllib.urlretrieve(url, dest, lambda nb, bs, fs, url = url: _pbhook(nb, bs, fs, url, dialog))
        def _pbhook(numblocks, blocksize, filesize, url = None,dialog = None):
            try:
                percent = min((numblocks * blocksize * 100) / filesize, 100)
                dialog.update(percent)
            except:
                percent = 100
                dialog.update(percent)
            if dialog.iscanceled():
                dialog.close()
        if __settings__.getSetting('download') == '':
            xbmc.executebuiltin("XBMC.Notification("+__language__(30000)+","+__language__(30015)+",5000,"+icon+")")
            __settings__.openSettings('download')
        filepath = xbmc.translatePath(os.path.join(__settings__.getSetting('download'),filename))
        download(url, filepath)


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


def addLink(name, url, desc, duration, iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration } )
        contextMenu = [('Download','XBMC.Container.Update(%s?url=%s&mode=9)' %(sys.argv[0], urllib.quote_plus(url)))]
        liz.addContextMenuItems(contextMenu)
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok


def addDir(name, url, mode, desc, iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&desc="+urllib.quote_plus(desc)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


params=get_params()
url=None
name=None
mode=None
iconimage=None
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
    desc=urllib.unquote_plus(params["desc"])
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
    addDir(__language__(30016),'http://www.archive.org/details/audio',1,'','http://ia600304.us.archive.org/25/items/audio/audio.gif')
    addDir(__language__(30017),'http://www.archive.org/details/movies',1,'','http://ia700303.us.archive.org/0/items/movies/movies.gif')

elif mode==1:
    print "getCategories"
    getCategories(url, iconimage)

elif mode==2:
    print "getShowList"
    getShowList(url, iconimage)

elif mode==3:
    print "getMedia"
    getMedia(url, desc, iconimage)

elif mode==4:
    print "getBrowseByAuthor"
    getBrowseByAuthor(url, iconimage)

elif mode==5:
    print "getBrowseByTitle"
    getBrowseByTitle(url, iconimage)

elif mode==6:
    print "Search"
    Search(url, iconimage)

elif mode==7:
    print ""
    getBrowseKeyword(url, iconimage)

elif mode==8:
    print ""
    getBrowseLanguage(url, iconimage)

elif mode==9:
    print ""
    DownloadFiles(url)

elif mode==10:
    print ""
    getPlaylist(url, iconimage)

elif mode==11:
    print ""
    getBrowseByArtist(url, iconimage)

xbmcplugin.endOfDirectory(int(sys.argv[1]))	