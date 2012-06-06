import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from time import strftime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiterbroadcasting')
__language__ = __settings__.getLocalizedString

def CATEGORIES():
    # List all the shows.
    shows = {}

    # All Shows 
    shows[__language__(30006)] = {
        'feed': 'http://feeds2.feedburner.com/AllJupiterVideos?format=xml',
        'feed-low': 'http://feeds2.feedburner.com/AllJupiterVideos?format=xml',
        'image': 'http://images2.wikia.nocookie.net/__cb20110118004527/jupiterbroadcasting/images/2/24/JupiterBadgeGeneric.jpg',
        'plot': __language__(30206),
        'genre': 'Technology'
    }

    # Linux Action Show
    shows[__language__(30000)] = {
        'feed': 'http://feeds.feedburner.com/computeractionshowvideo',
        'feed-low': 'http://feeds.feedburner.com/linuxactionshowipodvid?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/LAS-VIDEO.jpg',
        'plot': __language__(30200),
        'genre': 'Technology'
    }

    # STOked
    shows[__language__(30002)] = {
        'feed': 'http://feeds.feedburner.com/stokedhd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/stokedipod?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/STOked-BadgeHD.png',
        'plot': __language__(30202),
        'genre': 'Technology'
    }

    # TechSnap
    shows[__language__(30008)] = {
        'feed': 'http://feeds.feedburner.com/techsnaphd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/techsnapmobile?format=xml',
        'image': 'http://images3.wikia.nocookie.net/jupiterbroadcasting/images/d/d6/Techsnapcenter.jpg',
        'plot': __language__(30208),
        'genre': 'Technology'
    }

    # SCIbyte
    shows[__language__(30009)] = {
        'feed': 'http://feeds.feedburner.com/scibytehd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/scibytemobile?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/SciByteBadgeHD.jpg',
        'plot': __language__(30209),
        'genre': 'Science'
    }

    # In Depth Look
    shows[__language__(30014)] = {
        'feed': 'http://www.jupiterbroadcasting.com/feeds/indepthlookihd.xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/indepthlookmob.xml',
        'image': 'http://images4.wikia.nocookie.net/jupiterbroadcasting/images/3/33/Indepthlook.jpg',
        'plot': __language__(30214),
        'genre': 'Technology'
    }

    # Unfilter
    shows[__language__(30016)] = {
        'feed': 'http://www.jupiterbroadcasting.com/feeds/unfilterHD.xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/unfilterMob.xml',
        'image': 'http://www.jupiterbroadcasting.com/images/itunes-badge.jpg',
        'plot': __language__(30216),
        'genre': 'Technology'
    }

    # FauxShow
    shows[__language__(30011)] = {
        'feed': 'http://blip.tv/fauxshow/rss/itunes',
        'feed-low': 'http://blip.tv/fauxshow/rss/itunes',
        'image': 'http://a.images.blip.tv/FauxShow-300x300_show_image205.png',
        'plot': __language__(30211),
        'genre': 'Humour'
    }

    # Jupiter@Nite
    shows[__language__(30004)] = {
        'feed': 'http://feeds.feedburner.com/jupiternitehd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/jupiternitehd?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/JANBADGE-LVID.jpg',
        'plot': __language__(30204),
        'genre': 'Technology'
    }

    # MMOrgue
    shows[__language__(30007)] = {
        'feed': 'http://feeds.feedburner.com/MMOrgueHD?format=xml',
        'feed-low': 'http://feeds.feedburner.com/MMOrgueHD?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/MMOrgueBadgeHD144.jpg',
        'plot': __language__(30207),
        'genre': 'Technology'
    }

    # LOTSO
    shows[__language__(30003)] = {
        'feed': 'http://feeds.feedburner.com/lotsovideo?format=xml',
        'feed-low': 'http://feeds.feedburner.com/lotsovideo?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/LOTSOiTunesVideo144.jpg',
        'plot': __language__(30203),
        'genre': 'Technology'
    }

    # Beer is Tasty
    shows[__language__(30001)] = {
        'feed': 'http://feeds2.feedburner.com/jupiterbeeristasty-hd?format=xml',
        'feed-low': 'http://feeds2.feedburner.com/jupiterbeeristasty-hd?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/beeristasty/BeerisTasty-iTunesBadgeHD.png',
        'plot': __language__(30201),
        'genre': 'Technology'
    }

    # Jupiter Files
    shows[__language__(30005)] = {
        'feed': 'http://feeds.feedburner.com/ldf-video?format=xml',
        'feed-low': 'http://feeds.feedburner.com/ldf-video?format=xml',
        'image': 'http://www.jupiterbroadcasting.com/images/LDF-FullStill144x139.jpg',
        'plot': __language__(30205),
        'genre': 'Technology'
    }

    # TORked
    shows[__language__(30015)] = {
        'feed': 'http://feeds.feedburner.com/TorkedHd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/TorkedMobile?format=xml',
        'image': 'http://images3.wikia.nocookie.net/jupiterbroadcasting/images/e/ea/Torked.jpg',
        'plot': __language__(30215),
        'genre': 'Technology'
    }

    # Jupiter Broadcasting Live via the RTMP stream
    addLink(__language__(30010), 'http://videocdn-us.geocdn.scaleengine.net/jblive-iphone/live/jblive.stream/playlist.m3u8', '', 'http://images2.wikia.nocookie.net/__cb20110118004527/jupiterbroadcasting/images/2/24/JupiterBadgeGeneric.jpg', {
        'title': __language__(30010),
        'plot': __language__(30210),
        'genre': 'Technology',
        'count': 1
    })

    # Loop through each of the shows and add them as directories.
    x = 2
    quality = int(__settings__.getSetting("video_quality"))
    for name, data in shows.iteritems():
        data['count'] = x
        x = x + 1
        # Check whether to use the high or low quality feed.
        feed = data['feed'] # High by default.
        if (quality == 1):
            feed = data['feed-low']
        addDir(name, feed, 1, data['image'], data)

def INDEX(name, url):
    # Load the XML feed.
    data = urllib2.urlopen(url)

    # Parse the data with BeautifulStoneSoup, noting any self-closing tags.
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES, selfClosingTags=['media:thumbnail', 'enclosure', 'media:content'])
    count = 1
    # Wrap in a try/catch to protect from borken RSS feeds.
    try:
        for item in soup.findAll('item'):
            # Load up the initial episode information.
            info = {}
            title = item.find('title')
            info['title'] = str(count) + '. '
            if (title):
                info['title'] += title.string
            info['tvshowtitle'] = name
            info['count'] = count
            count += 1 # Increment the show count.

            # Get the video enclosure.
            video = ''
            enclosure = item.find('enclosure')
            if (enclosure != None):
                video = enclosure.get('href')
                if (video == None):
                    video = enclosure.get('url')
                if (video == None):
                    video = ''
                size = enclosure.get('length')
                if (size != None):
                    info['size'] = int(size)

            # TODO: Parse the date correctly.
            date = ''
            pubdate = item.find('pubDate')
            if (pubdate != None):
                date = pubdate.string
                # strftime("%d.%m.%Y", item.updated_parsed)

            # Plot outline.
            summary = item.find('itunes:summary')
            if (summary != None):
                info['plot'] = info['plotoutline'] = summary.string.strip()

            # Plot.
            description = item.find('description')
            if (description != None):
                # Attempt to strip the HTML tags.
                try:
                    info['plot'] = re.sub(r'<[^>]*?>', '', description.string)
                except:
                    info['plot'] = description.string

            # Author/Director.
            author = item.find('itunes:author')
            if (author != None):
                info['director'] = author.string

            # Load the self-closing media:thumbnail data.
            thumbnail = ''
            mediathumbnail = item.findAll('media:thumbnail')
            if (mediathumbnail):
                thumbnail = mediathumbnail[0]['url']

            # Add the episode link.
            addLink(info['title'], video, date, thumbnail, info)
    except:
       pass

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

# Info takes Plot, date, size
def addLink(name, url, date, iconimage, info):
        ok=True
        liz=xbmcgui.ListItem(name, date, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="video", infoLabels=info )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addDir(name, url, mode, iconimage, info):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    info["Title"] = name
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="video", infoLabels=info)
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
        CATEGORIES()

elif mode==1:
        print ""+url
        INDEX(name, url)


xbmcplugin.endOfDirectory(int(sys.argv[1]))

