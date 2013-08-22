import urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, os
from time import strftime
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiterbroadcasting')
__language__ = __settings__.getLocalizedString

def CATEGORIES():
    # List all the shows.
    shows = {}
    quality = int(__settings__.getSetting("video_quality"))

    # All Shows
    shows[__language__(30006)] = {
        'feed': 'http://feeds2.feedburner.com/AllJupiterVideos?format=xml',
        'feed-low': 'http://feeds2.feedburner.com/AllJupiterVideos?format=xml',
        'feed-audio': 'http://feeds2.feedburner.com/AllJupiterBroadcastingShowsOgg?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'jupiterbroadcasting.jpg'),
        'plot': __language__(30206),
        'genre': 'Technology',
        'count': 0
    }

    # Linux Action Show
    shows[__language__(30000)] = {
        'feed': 'http://feeds.feedburner.com/computeractionshowvideo',
        'feed-low': 'http://feeds.feedburner.com/linuxactionshowipodvid?format=xml',
        'feed-audio': 'http://feeds2.feedburner.com/TheLinuxActionShowOGG?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'linuxactionshow.jpg'),
        'plot': __language__(30200),
        'genre': 'Technology'
    }

    # STOked
    shows[__language__(30002)] = {
        'feed': 'http://feeds.feedburner.com/stokedhd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/stokedipod?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/stoked-ogg?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'stoked.png'),
        'plot': __language__(30202),
        'genre': 'Technology'
    }

    # TechSnap
    shows[__language__(30008)] = {
        'feed': 'http://feeds.feedburner.com/techsnaphd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/techsnapmobile?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/techsnapogg?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'techsnap.jpg'),
        'plot': __language__(30208),
        'genre': 'Technology'
    }

    # SCIbyte
    shows[__language__(30009)] = {
        'feed': 'http://feeds.feedburner.com/scibytehd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/scibytemobile?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/scibyteaudio?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'scibyte.jpg'),
        'plot': __language__(30209),
        'genre': 'Science'
    }

    # In Depth Look
    shows[__language__(30014)] = {
        'feed': 'http://www.jupiterbroadcasting.com/feeds/indepthlookihd.xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/indepthlookmob.xml',
        'feed-audio': 'http://www.jupiterbroadcasting.com/feeds/indepthlookmp3.xml?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'indepthlook.jpg'),
        'plot': __language__(30214),
        'genre': 'Technology'
    }

    # Unfilter
    shows[__language__(30016)] = {
        'feed': 'http://www.jupiterbroadcasting.com/feeds/unfilterHD.xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/unfilterMob.xml',
        'feed-audio': 'http://www.jupiterbroadcasting.com/feeds/unfilterogg.xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'unfilter.jpg'),
        'plot': __language__(30216),
        'genre': 'Technology'
    }

    # FauxShow
    shows[__language__(30011)] = {
        'feed': 'http://www.jupiterbroadcasting.com/feeds/FauxShowHD.xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/FauxShowMobile.xml',
        'feed-audio': 'http://www.jupiterbroadcasting.com/feeds/FauxShowMP3.xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'fauxshow.jpg'),
        'plot': __language__(30211),
        'genre': 'Comedy'
    }

    # Jupiter@Nite
    shows[__language__(30004)] = {
        'feed': 'http://feeds.feedburner.com/jupiternitehd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/jupiternitelargevid?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/jupiternitemp3?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'jupiteratnite.jpg'),
        'plot': __language__(30204),
        'genre': 'Technology'
    }

    # MMOrgue
    shows[__language__(30007)] = {
        'feed': 'http://feeds.feedburner.com/MMOrgueHD?format=xml',
        'feed-low': 'http://feeds.feedburner.com/MMOrgueHD?format=xml',
        'feed-audio': 'http://www.jupiterbroadcasting.com/feeds/AllJupiterBroadcastingShowsOGG.xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'mmorgue.jpg'),
        'plot': __language__(30207),
        'genre': 'Technology'
    }

    # LOTSO
    shows[__language__(30003)] = {
        'feed': 'http://feeds.feedburner.com/lotsovideo?format=xml',
        'feed-low': 'http://feeds.feedburner.com/lotsovideo?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/lotsomp3?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'lotso.jpg'),
        'plot': __language__(30203),
        'genre': 'Technology'
    }

    # Beer is Tasty
    shows[__language__(30001)] = {
        'feed': 'http://feeds2.feedburner.com/jupiterbeeristasty-hd?format=xml',
        'feed-low': 'http://feeds2.feedburner.com/BeerIsTasty?format=xml',
        'feed-audio': 'http://feeds2.feedburner.com/BeerIsTasty?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'beeristasty.png'),
        'plot': __language__(30201),
        'genre': 'Technology'
    }

    # Jupiter Files
    shows[__language__(30005)] = {
        'feed': 'http://feeds.feedburner.com/ldf-video?format=xml',
        'feed-low': 'http://feeds.feedburner.com/ldf-video?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/ldf-mp3?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'jupiterfiles.jpg'),
        'plot': __language__(30205),
        'genre': 'Technology'
    }

    # TORked
    shows[__language__(30015)] = {
        'feed': 'http://feeds.feedburner.com/TorkedHd?format=xml',
        'feed-low': 'http://feeds.feedburner.com/TorkedMobile?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/TorkedMp3?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'torked.jpg'),
        'plot': __language__(30215),
        'genre': 'Technology'
    }

    # Coder Radio
    shows[__language__(30017)] = {
        'feed': 'http://feeds.feedburner.com/coderradiovideo?format=xml',
        'feed-low': 'http://www.jupiterbroadcasting.com/feeds/coderradioogg.xml?format=xml',
        'feed-audio': 'http://www.jupiterbroadcasting.com/feeds/coderradioogg.xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'coderradio.jpg'),
        'plot': __language__(30217),
        'genre': 'Technology'
    }

    # Plan B
    shows[__language__(30018)] = {
        'feed': 'http://feeds.feedburner.com/PlanBVideo?format=xml',
        'feed-low': 'http://feeds.feedburner.com/planbogg?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/planbogg?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'planb.jpg'),
        'plot': __language__(30218),
        'genre': 'Technology'
    }

    # Linux Unplugged
    shows[__language__(30019)] = {
        'feed': 'http://feeds.feedburner.com/linuxunvid?format=xml',
        'feed-low': 'http://feeds.feedburner.com/linuxunogg?format=xml',
        'feed-audio': 'http://feeds.feedburner.com/linuxunogg?format=xml',
        'image': os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'linuxunplugged.jpg'),
        'plot': __language__(30219),
        'genre': 'Technology'
    }

    # Jupiter Broadcasting Live via the HLS/RTMP stream
    liveUrl = 'http://videocdn-us.geocdn.scaleengine.net/jblive-iphone/live/jblive.stream/playlist.m3u8'
    if (quality == 1):
        liveUrl = 'rtsp://videocdn-us.geocdn.scaleengine.net/jblive/live/jblive.stream'
    elif (quality == 2):
        liveUrl = 'http://www.jupiterbroadcasting.com/listen/jbradiofm.m3u'
    addLink(
        name = __language__(30010),
        url = liveUrl,
        date = '',
        iconimage = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'jupiterbroadcasting.jpg'),
        info = {
            'title': __language__(30010),
            'plot': __language__(30210),
            'genre': 'Technology',
            'count': 1
        }
    )

    # Loop through each of the shows and add them as directories.
    x = 2
    for name, data in shows.iteritems():
        # @TODO Get the ordering correct.
        data['count'] = x
        x = x + 1
        # Check whether to use the high or low quality feed.
        feed = data['feed'] # High by default.
        if (quality == 1):
            feed = data['feed-low']
        elif (quality == 2):
            feed = data['feed-audio']
        addDir(name, feed, 1, data['image'], data)

def INDEX(name, url, page):
    # Load the XML feed.
    data = urllib2.urlopen(url)

    # Parse the data with BeautifulStoneSoup, noting any self-closing tags.
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES, selfClosingTags=['media:thumbnail', 'enclosure', 'media:content'])
    count = 1

    # Figure out where to start and where to stop the pagination.
    # TODO: Fix the Episodes per Page setting.
    episodesperpage = int(float(__settings__.getSetting("episodes_per_page")))
    start = episodesperpage * int(page);
    print "Episodes per Page: " + str(episodesperpage) + "\n"
    print "Start:" + str(start);
    n = 0;

    # Wrap in a try/catch to protect from broken RSS feeds.
    try:
        for item in soup.findAll('item'):
            # Set up the pagination properly.
            n += 1
            if (n < start):
                # Skip this episode since it's before the page starts.
                continue
            if (n >= start + episodesperpage):
                # Add a go to next page link, and skip the rest of the loop.
                addDir(
                    name = __language__(30300),
                    url = url,
                    mode= 1,
                    iconimage = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'next.png'),
                    info = {},
                    page = page + 1
                )
                break

            # Load up the initial episode information.
            info = {}
            title = item.find('title')
            info['title'] = str(n) + '. '
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
    xbmcplugin.setContent(int( sys.argv[1] ), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

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
        liz = xbmcgui.ListItem(name, date, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setProperty('IsPlayable', 'true')
        liz.setInfo(type="Video", infoLabels = info)
        return xbmcplugin.addDirectoryItem(
            handle = int(sys.argv[1]),
            url = url,
            listitem = liz,
            isFolder = False
        )

def addDir(name, url, mode, iconimage, info, page = 0):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name) + "&page="+str(page)
    ok=True
    info["Title"] = name
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="video", infoLabels=info)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

params = get_params()
url = None
name = None
mode = None
page = None

try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass
try:
        page = int(params["page"])
except:
        page = 0

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "Page: "+str(page)

if mode==None or url==None or len(url)<1:
        CATEGORIES()
elif mode==1:
        INDEX(name, url, page)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

