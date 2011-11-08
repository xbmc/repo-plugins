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
sort = __settings__.getSetting('sort_by')
if sort==__language__(30009):
    set = 'publicdate'
elif sort==__language__(30010):
    set = 'date'
elif sort==__language__(30011):
    set = 'downloads'
elif sort==__language__(30012):
    set = 'avg_rating%3B-num_reviews'
else:
    set = 'publicdate'


def getResponse(url):
        try:
            req = urllib2.Request(url)
            req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
            response = urllib2.urlopen(req)
            link = response.read()
            response.close()
            return link
        except urllib2.URLError, e:
            errorStr = str(e.read())
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification("+__language__(30028)+","+__language__(30029)+str(e.code)+",5000,"+icon+")")
            return


def getCategories():
        addDir(__language__(30005),'getLiveArchive',4,icon)
        addDir(__language__(30001),'getAudioBooks',5,icon)
        addDir(__language__(30024),'getRadioPrograms',9,icon)
        addDir(__language__(30006),'getMusicArts',10,icon)
        addDir(__language__(30025),'http://www.archive.org/search.php?query=collection%3AGratefulDead&sort=-'+set,1,icon)
        addDir(__language__(30002),'http://www.archive.org/search.php?query=collection%3Aopensource_audio&sort=-'+set,1,icon)
        addDir(__language__(30004),'http://www.archive.org/search.php?query=collection%3Aaudio_tech&sort=-'+set,1,icon)
        addDir(__language__(30013),'http://www.archive.org/search.php?query=collection%3Anetlabels&sort=-'+set,1,icon)
        addDir(__language__(30014),'http://www.archive.org/search.php?query=collection%3Aaudio_news&sort=-'+set,1,icon)
        addDir(__language__(30015),'http://www.archive.org/search.php?query=collection%3Aaudio_foreign&sort=-'+set,1,icon)
        addDir(__language__(30017),'http://www.archive.org/search.php?query=collection%3Aaudio_religion&sort=-'+set,1,icon)


def getLiveArchive():
        addDir(__language__(30020),'etree',8,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        addDir(__language__(30000),'getArtist',3,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        url = 'http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-'+set
        link = getResponse(url)
        match = re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>').findall(link)
        for url,name in match:
            addDir(name,'http://www.archive.org'+url,2,icon)
        page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)[0].replace('&amp;','&')
        addDir(__language__(30016),'http://www.archive.org'+page,1,xbmc.translatePath(os.path.join(home, 'resources', 'next.png')))


def getAudioBooks():
        addDir(__language__(30020),'audio_bookspoetry',8,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        addDir(__language__(30007),'audio_bookspoetry',6,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        addDir(__language__(30018),'http://www.archive.org/details/audio_bookspoetry',7,icon)
        getSubCategories('http://www.archive.org/details/audio_bookspoetry')
        url='http://www.archive.org/search.php?query=collection%3Aaudio_bookspoetry&sort=-'+set
        getShows(url)


def getRadioPrograms():
        addDir(__language__(30020),'radioprograms',8,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        addDir(__language__(30007),'radioprograms',6,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        getSubCategories('http://www.archive.org/details/radioprograms')
        url='http://www.archive.org/search.php?query=collection%3Aradioprograms&sort=-'+set
        getShows(url)


def getMusicArts():
        addDir(__language__(30020),'audio_music',8,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        addDir(__language__(30007),'audio_music',6,xbmc.translatePath(os.path.join(home, 'resources', 'search.png')))
        getSubCategories('http://www.archive.org/details/audio_music')
        url='http://www.archive.org/search.php?query=collection%3Aaudio_music&sort=-'+set
        getShows(url)


def getSubCategories(url):
        soup = BeautifulSoup(getResponse(url))
        items = soup.findAll('div', attrs={'style' : "padding:10px;"})
        for i in items:
            name = i.a.string
            url = i.a['href']
            desc = i.br.next
            url = url.replace('/details/','/search.php?query=collection%3A')
            if name.startswith('Gutenberg'):
                url = '/search.php?query=%28format%3Amp3%20AND%20collection%3Agutenberg%29%20AND%20-mediatype%3Acollection'
            addDir(name+' ) '+desc.encode('ascii', 'ignore'),'http://www.archive.org'+url+'&sort=-'+set,1,icon)


# get by artist listings
def getArtist():
        url='http://www.archive.org/browse.php?collection=etree&field=%2Fmetadata%2Fcreator'
        soup = BeautifulSoup(getResponse(url))
        match=re.compile('href="(.+?)">(.+?)</a>, <a href=".+?">(.+?)</a>').findall(str(soup.find('tr', attrs={'valign' : 'top'}).findAll('a')))
        for url,name,shows in match:
            url=url.replace('/details/','/search.php?query=collection%3A')
            addDir(name+'  | '+shows,'http://www.archive.org'+url+'&sort=-'+set,1,icon)


# get the directories		
def getShows(url):
        link = getResponse(url)
        match=re.compile('<a class="titleLink" href="(.+?)">(.+?)</a>.+?<br/>(.+?)</td>').findall(link)
        for url,name,desc in match:
            name=name.replace('<span class="searchTerm">','').replace('</span>','').replace('&amp;','&')
            addDir(name,'http://www.archive.org'+url,2,icon)
        try:
            page=re.compile('</a> &nbsp;&nbsp;&nbsp; <a href="(.+?)">Next</a>').findall(link)[0].replace('&amp;','&')
            addDir(__language__(30016),'http://www.archive.org'+page,1,xbmc.translatePath(os.path.join(home, 'resources', 'next.png')))
        except:
            pass


# gets names and urls	
def playMusic(title, url):
        link = getResponse(url)
        try:
            thumb = re.compile('<img title="\[item image\]" alt="\[item image\]" style="max-height:152px; max-width:165px; margin-bottom:0.5em; border:0px;" id="thumbnail" src="(.+?)"/>').findall(link)[0]
        except:
            try:
                thumb = re.compile('<a href=".+?"><img title=".+?" alt=".+?" id=".+?" src="(.+?)"/></a>').findall(link)[0]
            except:
                thumb = icon
        if thumb.startswith('/'):
            thumb = 'http://www.archive.org'+thumb
        try:
            soupA = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
            downloads = soupA('p', attrs={'id' : "dl"})[0]('a')
            for i in downloads:
                type = i.string
                href = i['href']
                try:
                    size = i.fetchPrevious('span')[0].string
                    if 'NEW' in size:
                        size = ''
                except:
                    size = ''
                if href[-3:] == 'zip':
                    # add Download listitem
                    u=sys.argv[0]+"?url="+urllib.quote_plus('http://www.archive.org'+href)+"&mode=11&name="+urllib.quote_plus(__language__(30026)+type+' '+size)+"&title="+urllib.quote_plus(title.replace(' ','_'))
                    ok=True
                    liz=xbmcgui.ListItem(__language__(30026)+type+' '+size, iconImage="DefaultFolder.png", thumbnailImage=xbmc.translatePath(os.path.join(home, 'resources', 'download.png')))
                    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        except:
            pass

        try:
            match = re.compile("IAD.mrss = '(.+?)'").findall(link)[0]
            soup = BeautifulStoneSoup(match, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
            if len(soup('item')) > 1:
                #add Play All listitem
                u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=12&name="+urllib.quote_plus(__language__(30027))
                ok=True
                liz=xbmcgui.ListItem(__language__(30027), iconImage="DefaultFolder.png", thumbnailImage=xbmc.translatePath(os.path.join(home, 'resources', 'play.png')))
                ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)

            for i in soup('item'):
                name = urllib.unquote_plus(i('media:title')[0].string.encode("utf-8", 'ignore'))
                url = i ('media:content')[0]['url']
                try:
                    duration = i('media:content')[0]['duration']
                except:
                    duration = ''
                addLink(name, 'http://www.archive.org'+url, duration, thumb)
        except:
            pass


def getPlaylist(url):
        link = getResponse(url)
        try:
            thumb = re.compile('<img title="\[item image\]" alt="\[item image\]" style="max-height:152px; max-width:165px; margin-bottom:0.5em; border:0px;" id="thumbnail" src="(.+?)"/>').findall(link)[0]
        except:
            try:
                thumb = re.compile('<a href=".+?"><img title=".+?" alt=".+?" id=".+?" src="(.+?)"/></a>').findall(link)[0]
            except:
                thumb = icon
        if thumb.startswith('/'):
            thumb = 'http://www.archive.org'+thumb

        player = xbmc.Player()
        if player.isPlaying():
            player.stop()
        playlist = xbmc.PlayList(0)
        playlist.clear()

        match = re.compile("IAD.mrss = '(.+?)'").findall(link)[0]
        soup = BeautifulStoneSoup(match, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        for i in soup('item'):
            name = urllib.unquote_plus(i('media:title')[0].string.encode("ascii", 'ignore'))
            url = i ('media:content')[0]['url']
            try:
                duration = i('media:content')[0]['duration']
            except:
                duration = ''
            liz=xbmcgui.ListItem(name, iconImage=thumb, thumbnailImage=thumb)
            liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration } )
            playlist.add(url='http://www.archive.org'+url, listitem=liz)
        xbmc.executebuiltin('playlist.playoffset(music,0)')

def DownloadFiles(title,url):
        filename = title+'.zip'
        def download(url, dest):
            dialog = xbmcgui.DialogProgress()
            dialog.create(__settings__.getLocalizedString(30022), __settings__.getLocalizedString(30023), filename)
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
            __settings__.openSettings('download')
        filepath = xbmc.translatePath(os.path.join(__settings__.getSetting('download'),filename))
        download(url, filepath)


def Search(url):
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
        getShows(url)


def searchByTitle(url):
        url='http://www.archive.org/details/'+url
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browsetitle"})[0]('a')
        for i in items:
            href = i['href']
            name = i.string
            url = 'http://www.archive.org'+href.replace(' ','%20')
            addDir(name,url,1,icon)


# search audio books by author
def searchByAuthor():
        url='http://www.archive.org/details/audio_bookspoetry'
        soup = BeautifulSoup(getResponse(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'id' : "browsetitle"})[0]('a')
        for i in items:
            href = i['href']
            name = i.string
            url = 'http://www.archive.org'+href.replace(' ','%20').replace('sort=title','sort=creator').replace('firstTitle','firstCreator')
            addDir(name,url,1,icon)


def addLink(name,url,duration,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="video", infoLabels={ "Title": name, "Duration": duration } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
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
    title=urllib.unquote_plus(params["title"])
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
    getCategories()

elif mode==1:
    print ""
    getShows(url)

elif mode==2:
    print ""
    playMusic(name, url)

elif mode==3:
    print ""
    getArtist()

elif mode==4:
    print ""
    getLiveArchive()

elif mode==5:
    print ""
    getAudioBooks()

elif mode==6:
    print ""
    searchByTitle(url)

elif mode==7:
    print ""
    searchByAuthor()

elif mode==8:
    print ""
    Search(url)	

elif mode==9:
    print ""
    getRadioPrograms()

elif mode==10:
    print ""
    getMusicArts()

elif mode==11:
    print ""
    DownloadFiles(title,url)

elif mode==12:
    print ""
    getPlaylist(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))	