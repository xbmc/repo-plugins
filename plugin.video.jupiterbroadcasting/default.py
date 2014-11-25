#!/usr/bin/env python
"""
Jupiter Broadcasting XBMC Addon
http://github.com/robloach/plugin.video.jupiterbroadcasting
"""

import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, os
from BeautifulSoup import BeautifulStoneSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiterbroadcasting')
__language__ = __settings__.getLocalizedString

def get_shows():
    """
    List of available Jupiter Broadcasting shows.
    """
    shows = {}
    feedburner = 'http://feeds2.feedburner.com/'
    jupiter = 'http://www.jupiterbroadcasting.com/'

    # All Shows
    shows[__language__(30006)] = {
        'feed': feedburner + 'AllJupiterVideos?format=xml',
        'feed-low': feedburner + 'AllJupiterVideos?format=xml',
        'feed-audio': feedburner + '/AllJupiterBroadcastingShowsOgg?format=xml',
        'image': 'most-recent.jpg',
        'plot': __language__(30206),
        'genre': 'Technology',
        'count': 0
    }

    # Linux Action Show
    shows[__language__(30000)] = {
        'feed': feedburner + 'linuxashd?format=xml',
        'feed-low': feedburner + 'linuxactionshowipodvid?format=xml',
        'feed-audio': feedburner + 'TheLinuxActionShowOGG?format=xml',
        'image': 'linux-action-show.jpg',
        'plot': __language__(30200),
        'genre': 'Technology'
    }

    # STOked
    shows[__language__(30002)] = {
        'feed': feedburner + 'stokedhd?format=xml',
        'feed-low': feedburner + 'stokedipod?format=xml',
        'feed-audio': feedburner + 'stoked-ogg?format=xml',
        'image':'stoked.png',
        'plot': __language__(30202),
        'genre': 'Technology'
    }

    # TechSnap
    shows[__language__(30008)] = {
        'feed': feedburner + 'techsnaphd?format=xml',
        'feed-low': feedburner + 'techsnapmobile?format=xml',
        'feed-audio': feedburner + 'techsnapogg?format=xml',
        'image': 'techsnap.jpg',
        'plot': __language__(30208),
        'genre': 'Technology'
    }

    # SCIbyte
    shows[__language__(30009)] = {
        'feed': feedburner + 'scibytehd?format=xml',
        'feed-low': feedburner + 'scibytemobile?format=xml',
        'feed-audio': feedburner + 'scibyteaudio?format=xml',
        'image': 'scibyte.jpg',
        'plot': __language__(30209),
        'genre': 'Science'
    }

    # In Depth Look
    shows[__language__(30014)] = {
        'feed': jupiter + 'feeds/indepthlookihd.xml',
        'feed-low': jupiter + 'feeds/indepthlookmob.xml',
        'feed-audio': jupiter + 'feeds/indepthlookmp3.xml?format=xml',
        'image': 'in-depth-look.jpg',
        'plot': __language__(30214),
        'genre': 'Technology'
    }

    # Unfilter
    shows[__language__(30016)] = {
        'feed': jupiter + 'feeds/unfilterHD.xml',
        'feed-low': jupiter + 'feeds/unfilterMob.xml',
        'feed-audio': jupiter + 'feeds/unfilterogg.xml',
        'image': 'unfilter.jpg',
        'plot': __language__(30216),
        'genre': 'Technology'
    }

    # FauxShow
    shows[__language__(30011)] = {
        'feed': jupiter + 'feeds/FauxShowHD.xml',
        'feed-low': jupiter + 'feeds/FauxShowMobile.xml',
        'feed-audio': jupiter + 'feeds/FauxShowMP3.xml',
        'image': 'faux-show.jpg',
        'plot': __language__(30211),
        'genre': 'Comedy'
    }

    # Jupiter@Nite
    shows[__language__(30004)] = {
        'feed': feedburner + 'jupiternitehd?format=xml',
        'feed-low': feedburner + 'jupiternitelargevid?format=xml',
        'feed-audio': feedburner + 'jupiternitemp3?format=xml',
        'image': 'jupiter-at-nite.jpg',
        'plot': __language__(30204),
        'genre': 'Technology'
    }

    # MMOrgue
    shows[__language__(30007)] = {
        'feed': feedburner + 'MMOrgueHD?format=xml',
        'feed-low': feedburner + 'MMOrgueHD?format=xml',
        'feed-audio': jupiter + 'feeds/AllJupiterBroadcastingShowsOGG.xml',
        'image': 'mmorgue.jpg',
        'plot': __language__(30207),
        'genre': 'Technology'
    }

    # LOTSO
    shows[__language__(30003)] = {
        'feed': feedburner + 'lotsovideo?format=xml',
        'feed-low': feedburner + 'lotsovideo?format=xml',
        'feed-audio': feedburner + 'lotsomp3?format=xml',
        'image': 'lotso.jpg',
        'plot': __language__(30203),
        'genre': 'Technology'
    }

    # Beer is Tasty
    shows[__language__(30001)] = {
        'feed': feedburner + 'jupiterbeeristasty-hd?format=xml',
        'feed-low': feedburner + 'BeerIsTasty?format=xml',
        'feed-audio': feedburner + 'BeerIsTasty?format=xml',
        'image': 'beer-is-tasty.png',
        'plot': __language__(30201),
        'genre': 'Technology'
    }

    # Jupiter Files
    shows[__language__(30005)] = {
        'feed': feedburner + 'ldf-video?format=xml',
        'feed-low': feedburner + 'ldf-video?format=xml',
        'feed-audio': feedburner + 'ldf-mp3?format=xml',
        'image': 'jupiter-files.jpg',
        'plot': __language__(30205),
        'genre': 'Technology'
    }

    # TORked
    shows[__language__(30015)] = {
        'feed': feedburner + 'TorkedHd?format=xml',
        'feed-low': feedburner + 'TorkedMobile?format=xml',
        'feed-audio': feedburner + 'TorkedMp3?format=xml',
        'image': 'torked.jpg',
        'plot': __language__(30215),
        'genre': 'Technology'
    }

    # Coder Radio
    shows[__language__(30017)] = {
        'feed': feedburner + 'coderradiovideo?format=xml',
        'feed-low': jupiter + 'feeds/coderradioogg.xml?format=xml',
        'feed-audio': jupiter + 'feeds/coderradioogg.xml',
        'image': 'coder-radio.jpg',
        'plot': __language__(30217),
        'genre': 'Technology'
    }

    # Plan B
    shows[__language__(30018)] = {
        'feed': feedburner + 'PlanBVideo?format=xml',
        'feed-low': feedburner + 'planbogg?format=xml',
        'feed-audio': feedburner + 'planbogg?format=xml',
        'image': 'planb.jpg',
        'plot': __language__(30218),
        'genre': 'Technology'
    }

    # Linux Unplugged
    shows[__language__(30019)] = {
        'feed': feedburner + 'linuxunvid?format=xml',
        'feed-low': feedburner + 'linuxunogg?format=xml',
        'feed-audio': feedburner + 'linuxunogg?format=xml',
        'image': 'linux-unplugged.jpg',
        'plot': __language__(30219),
        'genre': 'Technology'
    }

    # BSD Now
    shows[__language__(30020)] = {
        'feed': feedburner + 'BsdNowHd?format=xml',
        'feed-low': feedburner + 'BsdNowMobile?format=xml',
        'feed-audio': feedburner + 'BsdNowOgg?format=xml',
        'image': 'bsd-now.jpg',
        'plot': __language__(30220),
        'genre': 'Technology'
    }
    # HowTo Linux
    shows[__language__(30021)] = {
        'feed': feedburner + 'HowtoLinuxHd?format=xml',
        'feed-low': feedburner + 'HowtoLinuxMobile?format=xml',
        'feed-audio': feedburner + 'HowtoLinuxOgg?format=xml',
        'image': 'howto-linux.jpg',
        'plot': __language__(30221),
        'genre': 'Technology'
    }

    # Tech Talk Today
    shows[__language__(30022)] = {
        'feed': 'http://feedpress.me/t3mob',
        'feed-low': 'http://feedpress.me/t3ogg',
        'feed-audio': 'http://feedpress.me/t3ogg',
        'image': 'tech-talk-today.png',
        'plot': __language__(30222),
        'genre': 'Technology'
    }

    # Women's Tech Radio
    shows[__language__(30023)] = {
        'feed': feedburner + 'wtrmobile?format=xml',
        'feed-low': feedburner + 'wtrogg?format=xml',
        'feed-audio': feedburner + 'wtrmp3?format=xml',
        'image': 'womens-talk-radio.png',
        'plot': __language__(30223),
        'genre': 'Technology'
    }

    return shows

def categories():
    """
    Load the available categories for Jupiter Broadcasting.
    """
    # List all the shows.
    shows = get_shows()
    quality = int(__settings__.getSetting("video_quality"))
    scale = 'jblive.videocdn.scaleengine.net/'

    # Jupiter Broadcasting Live via the HLS/RTMP stream
    live_url = 'http://' + scale
    live_url += 'jblive-iphone/live/jblive.stream/playlist.m3u8'
    if quality == 1:
        live_url = 'rtsp://' + scale + 'jblive/live/jblive.stream'
    elif quality == 2:
        live_url = 'http://jblive.fm'
    add_link(
        name=__language__(30010),
        url=live_url,
        date='',
        iconimage=os.path.join(
            __settings__.getAddonInfo('path'),
            'resources',
            'media',
            'jblive-tv.jpg'),
        info={
            'title': __language__(30010),
            'plot': __language__(30210),
            'genre': 'Technology',
            'count': 1
        }
    )

    # Loop through each of the shows and add them as directories.
    iterator = 2
    for item_name, data in shows.iteritems():
        data['count'] = iterator
        iterator += 1
        # Check whether to use the high or low quality feed.
        feed = data['feed'] # High by default.
        if quality == 1:
            feed = data['feed-low']
        elif quality == 2:
            feed = data['feed-audio']
        data['image'] = os.path.join(
            __settings__.getAddonInfo('path'),
            'resources',
            'media',
            data['image'])
        add_dir(item_name, feed, 1, data['image'], data)

def index(name, url, page):
    """
    Presents a list of episodes within the given index page.
    """
    # Load the XML feed.
    data = urllib2.urlopen(url)

    # Parse the data with BeautifulStoneSoup, noting any self-closing tags.
    soup = BeautifulStoneSoup(
        data,
        convertEntities=BeautifulStoneSoup.XML_ENTITIES,
        selfClosingTags=['media:thumbnail', 'enclosure', 'media:content'])
    count = 1

    # Figure out where to start and where to stop the pagination.
    episodesperpage = int(float(__settings__.getSetting('episodes_per_page')))
    start = episodesperpage * int(page)
    currentindex = 0

    # Wrap in a try/catch to protect from broken RSS feeds.
    try:
        for item in soup.findAll('item'):
            # Set up the pagination properly.
            currentindex += 1
            if currentindex < start:
                # Skip this episode since it's before the page starts.
                continue
            if currentindex >= start + episodesperpage:
                # Add a go to next page link, and skip the rest of the loop.
                next_image = os.path.join(
                    __settings__.getAddonInfo('path'),
                    'resources',
                    'media',
                    'next.png')
                add_dir(
                    name=__language__(30300),
                    url=url,
                    mode=1,
                    iconimage=next_image,
                    info={},
                    page=page + 1)
                break

            # Load up the initial episode information.
            info = {}
            title = item.find('title')
            info['title'] = str(currentindex) + '. '
            if title:
                info['title'] += title.string
            info['tvshowtitle'] = name
            info['count'] = count
            count += 1 # Increment the show count.

            # Get the video enclosure.
            video = get_item_video(item, info)

            # Find the Date
            date = ''
            pubdate = item.find('pubDate')
            if pubdate != None:
                date = pubdate.string
                # strftime("%d.%m.%Y", item.updated_parsed)

            # Plot outline.
            summary = item.find('itunes:summary')
            if summary != None:
                info['plot'] = info['plotoutline'] = summary.string.strip()

            # Plot.
            get_item_description(item, info)

            # Author/Director.
            author = item.find('itunes:author')
            if author != None:
                info['director'] = author.string

            # Load the self-closing media:thumbnail data.
            thumbnail = ''
            mediathumbnail = item.findAll('media:thumbnail')
            if mediathumbnail:
                thumbnail = mediathumbnail[0]['url']

            # Add the episode link.
            add_link(info['title'], video, date, thumbnail, info)
    except:
        pass
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def get_item_description(item, info):
    description = item.find('description')
    if description != None:
        # Attempt to strip the HTML tags.
        try:
            info['plot'] = re.sub(r'<[^>]*?>', '', description.string)
        except:
            info['plot'] = description.string

def get_item_video(item, info):
    enclosure = item.find('enclosure')
    if enclosure != None:
        video = enclosure.get('href')
        if video == None:
            video = enclosure.get('url')
        if video == None:
            video = ''
        size = enclosure.get('length')
        if size != None:
            info['size'] = int(size)
    return video

def get_params():
    """
    Retrieves the current existing parameters from XBMC.
    """
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if params[len(params)-1] == '/':
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

# Info takes Plot, date, size
def add_link(name, url, date, iconimage, info):
    """
    Adds a link to XBMC's list of options.
    """
    liz = xbmcgui.ListItem(
        name,
        date,
        iconImage=iconimage,
        thumbnailImage=iconimage)
    liz.setProperty('IsPlayable', 'true')
    liz.setInfo(type='Video', infoLabels=info)
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=url,
        listitem=liz,
        isFolder=False)

def add_dir(name, url, mode, iconimage, info, page=0):
    """
    Adds a directory item to XBMC's list of options.
    """
    uri = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + str(mode)
    uri += '&name=' + urllib.quote_plus(name) + '&page=' + str(page)
    info['Title'] = name
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type='video', infoLabels=info)
    return xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]),
        url=uri,
        listitem=liz,
        isFolder=True)

PARAMS = get_params()
URL = None
NAME = None
MODE = None
PAGE = None

try:
    URL = urllib.unquote_plus(PARAMS["url"])
except:
    pass
try:
    NAME = urllib.unquote_plus(PARAMS["name"])
except:
    pass
try:
    MODE = int(PARAMS["mode"])
except:
    pass
try:
    PAGE = int(PARAMS["page"])
except:
    PAGE = 0

if MODE == None or URL == None or len(URL) < 1:
    categories()
elif MODE == 1:
    index(NAME, URL, PAGE)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
