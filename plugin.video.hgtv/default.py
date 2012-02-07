import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.hgtv')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')


def getRequest(url):
        headers = {'User-agent' : '	Mozilla/5.0 (Windows NT 6.1; WOW64; rv:10.0) Gecko/20100101 Firefox/10.0',
                   'Referer' : 'http://www.hgtv.com'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link
        
        
def getShows():
        url = 'http://www.hgtv.com/full-episodes/package/index.html'
        soup = BeautifulSoup(getRequest(url))
        shows = soup.findAll('ol', attrs={'id' : "fe-list"})[1]('li')
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
        addDir(__language__(30027),'getMoreShows',2,xbmc.translatePath( os.path.join( home, 'icon.png' ) ))


def getMoreShows():
        addDir(__language__(30000),'/hgtv-15-fresh-handmade-gift-ideas/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/11/09/sp100_15-fresh-homemade-gift-ideas_s994x100.jpg') # 15 Fresh Handmade Gift Ideas
        addDir(__language__(30001),'/hgtv-bang-for-your-buck/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/03/04/sp100-bang-for-the-buck.jpg') # Bang for Your Buck
        addDir(__language__(30002),'/hgtv-battle-on-the-block/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/03/10/spShow_battle-on-the-block_s994x100.jpg') # Battle On the Block
        addDir(__language__(30003),'/hgtv-behind-the-magic-disney-holidays/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/09/spShow_disney-holiday-special_s994x100.jpg') # Behind the Magic: Disney Holidays
        addDir(__language__(30004),'/candice-tells-all-full-episodes/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/12/14/spShow_candice-tells-all-v2_s994x100.jpg') # Candice Tells All
        addDir(__language__(30005),'/hgtv258/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/13/spShow_ctw-american-heroes_s994x200.jpg') # Change the World: American Heroes
        addDir(__language__(30006),'/hgtv-dinas-party/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/07/25/spShow_dinas-party_s994x100.jpg') # Dina's Party
        addDir(__language__(30007),'/hgtv-first-time-design/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/12/10/spShow_first-time-design_s994x100.jpg') # First Time Design
        addDir(__language__(30008),'/hgtv146/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_summerShowdown_v2.jpg') # HGTV Summer Showdown
        addDir(__language__(30009),'/hgtv236/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/04/16/sp200-250k-challenge-4.jpg') # HGTV's $250,000 Challenge
        addDir(__language__(30010),'/hgtv-hgtvs-great-rooms2/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/09/13/spShow_hgtv-great-rooms_s994x100.jpg') # HGTV's Great Rooms
        addDir(__language__(30011),'/hgtv-home-for-the-holidays/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp100-home-for-the-holidays.jpg') # HGTV's Home for the Holidays
        addDir(__language__(30012),'/hgtv-hgtv-the-making-of-our-magazine/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/08/12/spShow_making-of-our-magazine_s994x100.jpg') # HGTV: The Making of Our Magazine
        addDir(__language__(30013),'/hgtv-holmes-inspection/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/02/18/sp200_holmes-inspection_s994x200.jpg') # Holmes Inspection
        addDir(__language__(30014),'/hgtv-house-of-bryan/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/08/30/spShow_house-of-bryan_s994x100.jpg') # House of Bryan
        addDir(__language__(30015),'/hgtv-keys-to-the-castle/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/11/19/sp100-keys-to-the-castle-france.jpg') # Keys to the Castle, France
        addDir(__language__(30016),'/hgtv32/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_myHouseIsWorthWhat_v2.jpg') # My House Is Worth What?
        addDir(__language__(30017),'/hgtv-property-brothers/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/10/07/spShow_property-brothers_s994x100.jpg') # Property Brothers
        addDir(__language__(30018),'/hgtv-rv-2010/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/12/07/spShow_rv_s994x100.jpg') # RV
        addDir(__language__(30019),'/hgtv46/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_redHotandGreen_v2.jpg') # Red Hot & Green
        addDir(__language__(30020),'/hgtv-room-crashers/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/05/10/spShow_room-crashers_s994x100.jpg') # Room Crashers
        addDir(__language__(30021),'/hgtv-sandra-lee-celebrates/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/09/sp100_sandra-lee-celebrates-holiday-homecoming_s994x100.jpg') # Sandra Lee Celebrates: Holiday Homecoming
        addDir(__language__(30022),'/hgtv-sarah-101/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/06/03/spShow_sarah-101_s994x100.jpg') # Sarah 101
        addDir(__language__(30023),'/hgtv-sarahs-holiday-party/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/10/20/spShow_sarahs-holiday-party_s994x100.jpg') # Sarah's Holiday Party
        addDir(__language__(30024),'/hgtv-the-duchess/videos/index.html',1,'http://img.hgtv.com/HGTV/2009/10/07/spShow_the-duchess_s994x100.jpg') # The Duchess
        addDir(__language__(30025),'/hgtv-the-outdoor-room/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/11/23/spShow_the-outdoor-room-with-jamie-durie_s994x200.jpg') # The Outdoor Room With Jamie Durie
        addDir(__language__(30026),'/hgtv-white-house-christmas/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/11/23/spShow_white-house-xmas-2011_s994x100.jpg') # White House Christmas 2011


def INDEX(url, iconimage):
        if url.startswith('/'):
            url='http://www.hgtv.com'+url
        soup = BeautifulSoup(getRequest(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            if soup.find('ul', attrs={'class' : "channel-list"}):
                name = soup.find('ul', attrs={'class' : "channel-list"})('h4')[0]('em')[0].next
                url = soup.find('ul', attrs={'class' : "channel-list"})('a')[0]['href']
                addDir(name,url,1,iconimage)
                try:
                    seasons = soup.findAll('li', attrs={'class' : 'switch'})
                    for season in seasons:
                        name = season('h4')[0]('em')[0].next
                        url = season('a')[0]['href']
                        addDir(name,url,1,iconimage)
                except:
                    pass
        except:
                pass
        showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(str(soup))
        if len(showID)<1:
            showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(str(soup))
        if len(showID)<1:
            try:
                url = soup.find('ul', attrs={'class' : "button-nav"})('a')[1]['href']
                INDEX(url, iconimage)
            except:
                try:
                    url = soup.find('li', attrs={'class' : "tab-past-season"}).a['href']
                    INDEX(url, iconimage)
                except: print 'Houston we have a problem!'
        else:
            url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
            soup = BeautifulSoup(getRequest(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
            videos = soup('video')
            for video in videos:
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

if mode==None or url==None or len(url)<1:
    print ""
    getShows()

elif mode==1:
    print ""
    INDEX(url, iconimage)

elif mode==2:
    print ""
    getMoreShows()
    
xbmcplugin.endOfDirectory(int(sys.argv[1]))
