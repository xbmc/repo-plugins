import os
import sys
import urllib
import urllib2
import urlparse
import re
import xbmcgui
import xbmcplugin
import xbmcaddon
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

addon = xbmcaddon.Addon(id='plugin.video.linuxgamecast')
language = addon.getLocalizedString

defaultIconImage = os.path.join(addon.getAddonInfo('path'), 'icon.png')

SITE_URL = "http://linuxgamecast.com/"


def parse_args():
    p = urlparse.parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def index():
    quality = int(addon.getSetting("media_quality"))

    # Place Twitch stream listing at the top of the list.
    # Let Twitch plugin handle the video stream.
    lgclive = "plugin://plugin.video.twitch/playLive/linuxgamecast/"
    info = {
        "title": language(30006),
        "plot": language(30007),
        "plotline": language(30007),
        "director": language(30008),
        "genre": language(30009),
    }

    li = xbmcgui.ListItem(info["title"], path=lgclive, iconImage=defaultIconImage,
        thumbnailImage=defaultIconImage)
    li.setProperty("IsPlayable", "true")
    li.setInfo(type="Video", infoLabels=info)
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=lgclive, listitem=li, isFolder=False)

    # Place video category list next.
    showcategories = []
    
    # Latest
    category = {}
    category["title"] = language(30001)
    category["feed"] = "http://linuxgamecast.com/feed/"
    showcategories.append(category)

    # LinuxGameCast Weekly
    category = {}
    category["title"] = language(30002)
    category["feed"] = "http://linuxgamecast.com/category/linuxgamecastweekly/feed/"
    category["feed-hd"] = "http://linuxgamecast.com/feed/linuxgamecastweeklyvidhd/"
    showcategories.append(category)

    # L.G.C. Playas
    category = {}
    category["title"] = language(30003)
    category["feed"] = "http://linuxgamecast.com/category/l-g-c-playas/feed/"
    showcategories.append(category)

    # Reviews
    category = {}
    category["title"] = language(30004)
    category["feed"] = "http://linuxgamecast.com/category/reviews-2/feed/"
    showcategories.append(category)

    # B-Reel
    category = {}
    category["title"] = language(30005)
    category["feed"] = "http://linuxgamecast.com/category/b-reel/feed/"
    showcategories.append(category)

    for show in showcategories:
        feed = show["feed"]
        # Check if a category has an HD feed and
        # make sure that the user has opted to view the HD version.
        if (quality == 0 and "feed-hd" in show):
            feed = show["feed-hd"]

        u = build_url({"mode": "category", "url": feed})
        li = xbmcgui.ListItem(show["title"], iconImage="DefaultFolder.png")
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=li, isFolder=True)


def browseCategory(url):
    # Download feed.
    xbmc.log("Getting feed: {}".format(url), xbmc.LOGDEBUG)
    response = urllib2.urlopen(url)
    data = response.read()
    response.close()

    # Obtain relevant information from the RSS feed.
    soup = BeautifulStoneSoup(data, convertEntities=BeautifulStoneSoup.XML_ENTITIES)

    for item in soup.findAll('item'):
        info = {}
        info["title"] = item.find("title").string

        video = ""
        enclosure = item.find("enclosure")
        if (enclosure != None):
            video = enclosure.get("url")

            size = enclosure.get("length")
            if (size != None):
                info["size"] = int(size)

        date = ""
        pubdate = item.find("pubDate")
        if (pubdate != None):
            date = pubdata.string
        info["date"] = date

        summary = item.find("itunes:summary")
        if (summary != None):
            info["plot"] = summary.string.strip()
            info["plotoutline"] = summary.string.strip()

        description = item.find("description")
        if (description != None):
            # Attempt to strip the HTML tags.
            try:
                info['plot'] = re.sub(r'<[^>]*?>', '', description.string)
            except:
                info['plot'] = description.string

        author = item.find("itunes:author")
        if (author != None):
            info["director"] = author.string


        # If an RSS item has an enclosure tag, list it.
        if video:
            li = xbmcgui.ListItem(info["title"], date,
                iconImage=defaultIconImage, thumbnailImage=defaultIconImage)
            li.setProperty("IsPlayable", "true")
            li.setInfo(type="Video", infoLabels=info)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=video, listitem=li, isFolder=False)

    xbmcplugin.setContent(addon_handle, "episodes")


args = parse_args()

mode = args.get('mode', None)
url = args.get('url', None)

if mode == "category" and url != None:
    browseCategory(url)
else:
    index()
 
xbmcplugin.endOfDirectory(addon_handle)

