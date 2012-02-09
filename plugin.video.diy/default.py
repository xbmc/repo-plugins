import urllib,urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.diy')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )

def getRequest(url):
        headers = {'User-agent' : '	Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0) Gecko/20100101 Firefox/10.0',
                   'Referer' : 'http://www.diynetwork.com'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link


def getShows():
        url = 'http://www.diynetwork.com/full-episodes/package/index.html'
        soup = BeautifulSoup(getRequest(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows = soup('div', attrs={'id' : "full-episodes"})[0]('li')[8:]
        Shows_list=[]
        for i in shows:
            name = i('img')[0]['alt']
            if name.startswith(' '):
                name = name[1:]
            url = i('a')[1]['href']
            thumbnail = i('img')[0]['src'].replace(' ','')
            show = (name, url, thumbnail)
            if not show in Shows_list:
                Shows_list.append(show)
        for i in Shows_list:
            addDir(i[0], i[1], 1, i[2])
        addDir(__language__(30019),'getMoreShows',2,icon)


def getMoreShows():
        addDir(__language__(30000),'/diy-10-killer-kitchen-projects/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/08/22/spShow_10-Killer-Kitchen-Projects_s994x100.jpg') #10 Killer Kitchen Projects
        addDir(__language__(30001),'/diy-americas-most-desperate-landscape2/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/02/16/spShow_AMDL_s994x200.jpg') #America's Most Desperate Landscape
        addDir(__language__(30002),'/diy-b-original-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/B-Original-sm-100.jpg') #B. Original
        addDir(__language__(30003),'/diy-backyard-blitz/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/23/spShow_Backyard-Blitz_s994x100.jpg') #Backyard Blitz
        addDir(__language__(30004),'/diy-backyard-stadiums/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/09/16/spShow_Backyard-Stadiums_s994x100.jpg') #Backyard Stadiums
        addDir(__language__(30005),'/diy-barkitecture/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/Barkitecture-sm-100.jpg') #Barkitecture
        addDir(__language__(30006),'/diy-cool-tools-inventors-challenge/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/23/spShow_cool-tools-inventors_s994x200.jpg') #Cool Tools: Inventor's Special
        addDir(__language__(30007),'/diy-diy-to-the-rescue-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/DIYToTheRescue-lg-100.jpg') #DIY to the Rescue
        addDir(__language__(30008),'/diy-desperate-landscapes-top-10/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/08/spShow_Desperate-Landscapes-Top-10_s994x200.jpg') #Desperate Landscapes Top 10
        addDir(__language__(30009),'/diy-dream-house-log-cabin/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/01/05/spShow_dream-house-log-cabin_s994x100.jpg') #Dream House Log Cabin
        addDir(__language__(30010),'/diy-esquires-ultimate-bachelor-pad/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/12/08/spShow_Esquires-Bachelor-Pad_s994x100.jpg') #Esquire's Ultimate Bachelor Pad
        addDir(__language__(30011),'/diy-fresh-from-the-garden/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/05/05/FreshFromTheGarden-sm-110.jpg') #Fresh from the Garden
        addDir(__language__(30012),'/diy-hammered/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/12/11/spShow_Hammered_s994x100.jpg') #Hammered With John & Jimmy DiResta
        addDir(__language__(30013),'/diy-haulin-house/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/27/haulinHouse-sm-100.jpg') #Haulin' House
        addDir(__language__(30014),'/diy-make-a-move-episode/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/MakeAMove-sm-101.jpg') #Make A Move
        addDir(__language__(30015),'/diy-studfinder/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/10/20/sp100_studfinder_s994x100.jpg') #Stud Finder
        addDir(__language__(30016),'/diy14/videos/index.html',1,'http://img.diynetwork.com/DIY/2009/04/24/KingOfDirt-lg-110.jpg') #The King of Dirt
        addDir(__language__(30017),'/diy-worst-kitchen-in-america/videos/index.html',1,'http://img.diynetwork.com/DIY/2011/01/07/spShow_Worst-Kitchen-In-America-cross-promo-vsn_s994x100.jpg') #Worst Kitchen in America
        addDir(__language__(30018),'/diy-yard-crashers-top-10/videos/index.html',1,'http://img.diynetwork.com/DIY/2010/02/08/spShow_Yard-Crashers-Top-10_s994x200.jpg') #Yard Crashers Top 10


def index(url, iconimage):
        url='http://www.diynetwork.com'+url
        soup = BeautifulSoup(getRequest(url))
        if soup.find('div', attrs={'id' : "more-videos-from-show"}):
            shows = soup.find('div', attrs={'id' : "more-videos-from-show"})('h4')
            for show in shows:
                name = show.string
                url = show.next.next.next('a')[0]['href']
                addDir(name,url,1,iconimage)
        showID=re.compile("var snap = new SNI.DIY.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(str(soup))
        if len(showID)<1:
            showID=re.compile("var snap = new SNI.DIY.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(str(soup))
        url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
        soup = BeautifulSoup(getRequest(url))
        for video in soup('video'):
            name = video('clipname')[0].string
            length = video('length')[0].string
            thumb = video('thumbnailurl')[0].string
            description = video('abstract')[0].string
            link = video('videourl')[0].string
            playpath = link.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
            url = 'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 swfUrl="http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf" playpath='+playpath
            addLink(name,url,description,length,thumb)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')


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


def addLink(name,url,description,length,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot":description, "Duration":length } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
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

if mode==None:
    print ""
    getShows()

elif mode==1:
    print ""
    index(url, iconimage)

elif mode==2:
    print ""
    getMoreShows()

xbmcplugin.endOfDirectory(int(sys.argv[1]))