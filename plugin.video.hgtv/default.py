import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.hgtv')
__language__ = __settings__.getLocalizedString

def getShows():
        addDir(__language__(30000), '/hgtv/on_tv/player/0,1000145,HGTV_32663_4621,00.html', 1, 'http://img.hgtv.com/HGTV/2009/04/16/cp60-250k-challenge.jpg')
        addDir(__language__(30001), '/hgtv-all-american-handyman/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/08/06/spFeature_american-handyman_s234x60.jpg')
        addDir(__language__(30002), '/hgtv-the-antonio-treatment/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2009/12/03/spFeature_the-antonio-treatment_s234x60.jpg')
        addDir(__language__(30003), '/hgtv-bang-for-your-buck/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/04/29/spFeature_bang-for-your-buck_s234x60.jpg')
        addDir(__language__(30004), '/hgtv160/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_carolDuvallShow.jpg')
        addDir(__language__(30005), '/hgtv246/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_CarterCan.jpg')
        addDir(__language__(30006), '/hgtv74/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-color-splash.png')
        addDir(__language__(30007), '/hgtv42/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-curb-appeal.png')
        addDir(__language__(30008), '/hgtv-curb-appeal-the-block2/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2009/12/10/cp60_curb-appeal-the-block_s234x60.jpg')
        addDir(__language__(30009), '/hgtv/on_tv/player/0,1000145,HGTV_32663_3541,00.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_dearGenevieve.jpg')
        addDir(__language__(30010), '/hgtv-deserving-design/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/31/cp60-deserving-design.jpg')
        addDir(__language__(30011), '/hgtv70/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-designed-to-sell.png')
        addDir(__language__(30012), '/hgtv8/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-gardening-by-the-yard.png')
        addDir(__language__(30013), '/hgtv262/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/11/02/cp60_for-rent_s234x60.jpg')
        addDir(__language__(30014), '/hgtv6/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-ground-breakers.png')
        addDir(__language__(30015), '/hgtv-hammerheads/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_hammerHeads.jpg')
        addDir(__language__(30016), '/dream-home/dream-home-videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/programguide_dreamhome2010.jpg')
        addDir(__language__(30017), '/hgtv176/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/programguide_greenhome2010.jpg')
        addDir(__language__(30018), '/hgtv-showdown/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2009/01/06/cp60-hgtv-showdown.jpg')
        addDir(__language__(30019), '/hgtv/on_tv/player/0,1000145,HGTV_32663_3381,00.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_HiddenPotential.jpg')
        addDir(__language__(30020), '/hgtv-holmes-on-homes/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/04/07/cp60_holmes-on-homes_s234x60.jpg')
        addDir(__language__(30021), '/hgtv-house-crashers/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/03/24/spFeature_house-crashers-hgtv_s234x60.jpg')
        addDir(__language__(30022), '/house-of-bryan/show/index.html', 1, 'http://img.hgtv.com/HGTV/2010/08/30/spFeature_house-of-bryan_s234x60.jpg')
        addDir(__language__(30023), '/hgtv-home-rules2/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/02/15/spFeature_home-rules_s234x60.jpg')
        addDir(__language__(30024), '/hgtv40/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-house-hunters.png')
        addDir(__language__(30025), '/hgtv56/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-house-hunters-int.png')
        addDir(__language__(30026), '/hgtv-income-property/videos/index.html', 1, ' http://img.hgtv.com/HGTV/2010/11/02/cp60_income-property_s234x60.jpg')
        addDir(__language__(30027), '/hgtv-keys-to-the-castle/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/31/cp60-keys-to-castle.jpg')
        addDir(__language__(30028), '/hgtv58/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-my-first-place.png')
        addDir(__language__(30029), '/hgtv-my-first-sale/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/10/27/spFeature_my-first-sale_s234x60.jpg')
        addDir(__language__(30030), '/hgtv32/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/11/07/cp60-my-house-is-worth-what.jpg')
        addDir(__language__(30031), '/hgtv18/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-myles-of-style.png')
        addDir(__language__(30032), '/hgtv60/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-national-open-house.png')
        addDir(__language__(30033), '/hgtv-the-outdoor-room/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2009/11/23/spFeature_the-outdoor-room-with-jamie-durie_s234x60.jpg')
        addDir(__language__(30034), '/hgtv/on_tv/player/0,1000145,HGTV_32663_3581,00.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_overYourHead.jpg')
        addDir(__language__(30035), '/paint-over/show/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/programguide_paint-over-with-jennifer-bertrand.jpg')
        addDir(__language__(30036), '/hgtv-professional-grade/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/09/17/spFeature_professional-grade_s234x60.jpg')
        addDir(__language__(30037), '/hgtv48/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/10/27/spFeature_property-virgins_s234x60.jpg')
        addDir(__language__(30038), '/hgtv176/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/10/27/spFeature_real-estate-intervention_s234x60.jpg')
        addDir(__language__(30039), '/hgtv46/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-red-hot-and-green.png')
        addDir(__language__(30040), '/hgtv2/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-rate-my-space.png')
        addDir(__language__(30041), '/hgtv-sarahs-house/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/01/06/cp60-sarahs-house_s234x60.jpg')
        addDir(__language__(30042), '/hgtv-selling-new-york/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/01/11/spFeature_selling-new-york_s234x60.jpg')
        addDir(__language__(30043), '/hgtv148/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2008/10/23/programguide_SimplyQuilts.jpg')
        addDir(__language__(30044), '/hgtv50/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-sleep-on-it.png')
        addDir(__language__(30045), '/hgtv24/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-spice-up-my-kitchen.png')
        addDir(__language__(30046), '/hgtv54/videos/index.html', 1, 'http://web.hgtv.com/webhgtv/hg20/imgs/full-epi/fe-the-stagers.png')
        addDir(__language__(30047), '/hgtv-tough-as-nails/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/04/01/spFeature_tough-as-nails_s234x60.jpg')
        addDir(__language__(30048), '/hgtv154/videos/index.html', 1, 'http://img.hgtv.com/HGTV/2010/11/02/cp60_yard-crashers_s234x60.jpg')
        
        
def INDEX(url):
        url='http://www.hgtv.com'+url
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://www.hgtv.com'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link)
        try:
                if soup.find('ul', attrs={'class' : "channel-list"}):
                        name = soup.find('ul', attrs={'class' : "channel-list"})('h4')[0]('em')[0].next
                        url = soup.find('ul', attrs={'class' : "channel-list"})('a')[0]['href']
                        addDir(name,url,1,'')
        except:
                pass
        showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(link)
        if len(showID)<1:
                showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(link)
        print'--------> '+showID[0]
        url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://www.hgtv.com'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link)
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
