import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.hgtv')
__language__ = __settings__.getLocalizedString


def getShows():
        addDir(__language__(30000),'/hgtv-15-fresh-handmade-gift-ideas/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/11/09/sp100_15-fresh-homemade-gift-ideas_s994x100.jpg')
        addDir(__language__(30001),'/hgtv-all-american-handyman/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/08/06/spShow_american-handyman_s994x100.jpg')
        addDir(__language__(30002),'/hgtv-bang-for-your-buck/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/03/04/sp100-bang-for-the-buck.jpg')
        addDir(__language__(30003),'/hgtv-battle-on-the-block/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/03/10/spShow_battle-on-the-block_s994x100.jpg')
        addDir(__language__(30004),'/hgtv-behind-the-magic-disney-holidays/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/09/spShow_disney-holiday-special_s994x100.jpg')
        addDir(__language__(30005),'/candice-tells-all-full-episodes/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/12/14/spShow_candice-tells-all-v2_s994x100.jpg')
        addDir(__language__(30006),'/hgtv246/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_carterCan.jpg')
        addDir(__language__(30007),'/hgtv-celebrity-holiday-homes/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/11/03/sp100_celebrity-holiday-homes_s994x100.jpg')
        addDir(__language__(30008),'/hgtv258/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/13/spShow_ctw-american-heroes_s994x200.jpg')
        addDir(__language__(30009),'/hgtv74/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/05/13/spShow_color-splash-2011_s994x100.jpg')
        addDir(__language__(30010),'/hgtv42/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_curbAppeal.jpg')
        addDir(__language__(30011),'/hgtv-curb-appeal-the-block2/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/12/10/sp100_curb-appeal-the-block_s994x100.jpg')
        addDir(__language__(30012),'/hgtv156/videos/index.html',1,'http://img.hgtv.com/HGTV/2008/10/17/showheader_dearGenevieve.jpg')
        addDir(__language__(30013),'/hgtv-deserving-design/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp200-deserving-design.jpg')
        addDir(__language__(30014),'/hgtv70/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_designedToSell.jpg')
        addDir(__language__(30015),'/hgtv-dinas-party/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/07/25/spShow_dinas-party_s994x100.jpg')
        addDir(__language__(30016),'/hgtv-first-time-design/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/12/10/spShow_first-time-design_s994x100.jpg')
        addDir(__language__(30017),'/hgtv262/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/03/13/sp100-for-rent.jpg')
        addDir(__language__(30018),'/hgtv8/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_gardeningByTheYard.jpg')
        addDir(__language__(30019),'/hgtv6/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_groundBreakers.jpg')
        addDir(__language__(30020),'/hgtv-showdown/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/01/06/sp200-hgtv-showdown.jpg')
        addDir(__language__(30021),'/hgtv146/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_summerShowdown_v2.jpg')
        addDir(__language__(30022),'/hgtv-hgtvd/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/12/15/spShow_hgtvd_s994x100.jpg')
        addDir(__language__(30023),'/hgtv236/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/04/16/sp200-250k-challenge-4.jpg')
        addDir(__language__(30024),'/hgtv-home-for-the-holidays/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp100-home-for-the-holidays.jpg')
        addDir(__language__(30025),'/hgtv-hammerheads/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_hammerHeads.jpg')
        addDir(__language__(30026),'/hgtv144/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_hiddenPotential_v2.jpg')
        addDir(__language__(30027),'/hgtv-holmes-inspection/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/02/18/sp200_holmes-inspection_s994x200.jpg')
        addDir(__language__(30028),'/hgtv-holmes-on-homes/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/04/17/sp200-holmes-on-homes.jpg')
        addDir(__language__(30029),'/hgtv-home-rules2/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/02/15/spShow_home-rules_s994x100.jpg')
        addDir(__language__(30030),'/hgtv-house-crashers/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/03/24/spShow_house-crashers-hgtv_s994x100.jpg')
        addDir(__language__(30031),'/hgtv40/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/02/01/spShow_house-hunters_s994x100.jpg')
        addDir(__language__(30032),'/hgtv56/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_houseHuntersInternational.jpg')
        addDir(__language__(30033),'/hgtv-house-hunters-on-vacation/videos/index.html',1,'http://img.hgtv.com/HGTV/2011/03/25/spShow_house-hunters-on-vacation_s994x100.jpg')
        addDir(__language__(30034),'/hgtv-house-of-bryan/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/08/30/spShow_house-of-bryan_s994x100.jpg')
        addDir(__language__(30035),'/hgtv-income-property/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp100-income-property.jpg')
        addDir(__language__(30036),'/hgtv-keys-to-the-castle/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/11/19/sp100-keys-to-the-castle-france.jpg')
        addDir(__language__(30037),'/hgtv58/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_myFirstPlace.jpg')
        addDir(__language__(30038),'/hgtv-my-first-sale/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/06/09/spShow_my-first-sale_s994x100.jpg')
        addDir(__language__(30039),'/hgtv32/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_myHouseIsWorthWhat_v2.jpg')
        addDir(__language__(30040),'/hgtv-my-yard-goes-disney/videos/index.html',1,'http://img.hgtv.com/HGTV/2011/05/06/spShow_my-yard-goes-disney_s994x100.jpg')
        addDir(__language__(30041),'/hgtv18/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp200-myles-of-style.jpg')
        addDir(__language__(30042),'/hgtv60/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_nationalOpenHouse.jpg')
        addDir(__language__(30043),'/hgtv162/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_overYourHead.jpg')
        addDir(__language__(30044),'/hgtv-professional-grade/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/09/17/spShow_professional-grade_s994x100.jpg')
        addDir(__language__(30045),'/hgtv48/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_propertyVirgins.jpg')
        addDir(__language__(30046),'/hgtv-rv-2010/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/12/01/spShow_rv-2011_s994x100.jpg')
        addDir(__language__(30047),'/hgtv2/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_RateMySpace.jpg')
        addDir(__language__(30048),'/hgtv176/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/06/10/sp100-real-estate-intervention.jpg')
        addDir(__language__(30049),'/hgtv46/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_redHotandGreen_v2.jpg')
        addDir(__language__(30050),'/hgtv-room-crashers/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/05/10/spShow_room-crashers_s994x100.jpg')
        addDir(__language__(30051),'/hgtv-sandra-lee-celebrates/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/10/09/sp100_sandra-lee-celebrates-holiday-homecoming_s994x100.jpg')
        addDir(__language__(30052),'/hgtv-sarah-101/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2011/06/03/spShow_sarah-101_s994x100.jpg')
        addDir(__language__(30053),'/hgtv-sarahs-holiday-party/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/10/20/spShow_sarahs-holiday-party_s994x100.jpg')
        addDir(__language__(30054),'/hgtv-sarahs-house/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/01/06/sp100-sarahs-house_s994x100.jpg')
        addDir(__language__(30055),'/hgtv-sarahs-summer-house/videos/index.html',1,'http://img.hgtv.com/HGTV/2011/02/10/spShow_sarahs-summer-house_s994x100.jpg')
        addDir(__language__(30056),'/hgtv-secrets-from-a-stylist2/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/08/23/spShow_secrets-from-a-stylist_s994x200.jpg')
        addDir(__language__(30057),'/hgtv-selling-new-york/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/01/11/spShow_selling-new-york_s994x100.jpg')
        addDir(__language__(30058),'/hgtv50/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/31/sp200-sleep-on-it.jpg')
        addDir(__language__(30059),'/hgtv24/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_spiceUpMyKitchen.jpg')
        addDir(__language__(30060),'/hgtv-the-antonio-treatment/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/01/12/spShow_the-antonio-treatment_s994x200.jpg')
        addDir(__language__(30061),'/hgtv-the-duchess/videos/index.html',1,'http://img.hgtv.com/HGTV/2009/10/07/spShow_the-duchess_s994x100.jpg')
        addDir(__language__(30062),'/hgtv-the-outdoor-room/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2009/11/23/spShow_the-outdoor-room-with-jamie-durie_s994x200.jpg')
        addDir(__language__(30063),'/hgtv54/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/10/17/showheader_theStagers.jpg')
        addDir(__language__(30064),'/hgtv-tough-as-nails/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2010/01/26/spShow_tough-as-nails_s994x100.jpg')
        addDir(__language__(30065),'/hgtv-white-house-christmas/videos/index.html',1,'http://img.hgtv.com/HGTV/2010/11/24/sp200_white-house-xmas-2010_s994x200.jpg')
        addDir(__language__(30066),'/hgtv154/videos/index.html',1,'http://hgtv.sndimg.com/HGTV/2008/12/09/sp200-yard-crashers.jpg')


def INDEX(url):
        url='http://www.hgtv.com'+url
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                   'Referer' : 'http://www.hgtv.com'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        try:
            if soup.find('ul', attrs={'class' : "channel-list"}):
                name = soup.find('ul', attrs={'class' : "channel-list"})('h4')[0]('em')[0].next
                url = soup.find('ul', attrs={'class' : "channel-list"})('a')[0]['href']
                addDir(name,url,1,'')
                try:
                    seasons = soup.findAll('li', attrs={'class' : 'switch'})
                    for season in seasons:
                        name = season('h4')[0]('em')[0].next
                        url = season('a')[0]['href']
                        addDir(name,url,1,'')
                except:
                    pass
        except:
                pass
        showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(link)
        if len(showID)<1:
            showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(link)
        url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
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
    print ""+url
    INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
