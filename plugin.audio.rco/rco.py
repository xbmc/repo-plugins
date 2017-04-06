# -*- coding: utf-8 -*-
# Step 1 - load kodi core support and setup the environment
import os
import xbmcplugin, xbmcaddon
import xbmc, xbmcgui
import sys
import urllib2
import re
import HTMLParser

xbmc.log("plugin.video.rco:: Starting Addon")


# magic; id of this plugin - cast to integer
thisPlugin = int(sys.argv[1])

# settings = xbmcaddon.Addon(id='plugin.audio.rco')
# The id is only necessary when you try to access other addons from your addon
settings = xbmcaddon.Addon()
IMG_DIR = os.path.join(settings.getAddonInfo("path"), "resources", "media")


# Step 2 - create the support functions (or classes)
def createListing():
    """
    Creates a listing that Kodi can display as a directory listing
    @return list
    """
    # url,name,metaname
    listing = []
    # listing.append(['RCO','http://rrr.sz.xlcdn.com/?account=RCOLiveWebradio&file=mp3-192&type=live&service=icecast&port=8000&output=pls'])
    URL = 'https://www.concertgebouworkest.nl/RCOradio'
    response = urllib2.urlopen(URL)
    html = response.read()
    rawlink = re.search(r'http.*?=pls', html).group(0)
    link = clean_links(rawlink)
    title = get_metadata(link).decode('iso-8859-1')
    elements = [title, link]
    elements += parse_metadata(title)
    listing.append(elements)
    return listing


def clean_links(lnk):
    html_parser = HTMLParser.HTMLParser()
    cleanlink = html_parser.unescape(lnk)
    return cleanlink


def get_metadata(cleanlink):
    request = urllib2.Request(cleanlink)
    try:
        request.add_header('Icy-MetaData', 1)
        response = urllib2.urlopen(request)
        icy_metaint_header = response.headers.get('icy-metaint')
        if icy_metaint_header is not None:
            metaint = int(icy_metaint_header)
            read_buffer = metaint+255
            content = response.read(read_buffer)
            title = content[metaint:].split("'")[1]
            return title
    except:
        xbmc.log("plugin.video.rco:: %s metadata error" % str(cleanlink))


def parse_metadata(title):
    elements = re.split('; | - |\: | \(|\n', title)
    try:
        year = re.search(r"(?<!\d)\d{4}(?!\d)", title).group(0)
        elements.append(year)
    except: pass
    return elements


def sendToKodi(listing):
    """
    Sends a listing to Kodi for display as a directory listing Plugins always result in a listing
    @param list listing
    @return void
    """

    # access global plugin id
    global thisPlugin

    # send each item to kodi
    for item in listing:
        listItem = xbmcgui.ListItem(item[0])
        listItem.setInfo('music', { 'genre': 'Classical', 'title': item[0], 'Artist': item[2], 'Album': item[3], 'comment': item[0], 'year': item[len(item) -1] })
        #listItem.setInfo(type="Music", infoLabels={"Title": item[0],
        #                                           "Artist": item[2],
        #                                           "Album": item[3],
        #                                           "Genre": "Classical",
        #                                           "Comment": item[0],
        #                                           "Year": item[len(item) - 1],
        #                                           # "AlbumArtist": item[4]
        #                                           })
        listItem.setArt({"thumb":os.path.join(IMG_DIR, "icon.png"), "fanart":os.path.join(IMG_DIR, "fanart.jpg")})
        xbmcplugin.addDirectoryItem(thisPlugin, item[1], listItem)

    # tell xbmc we have finished creating the directory listing
    xbmcplugin.endOfDirectory(thisPlugin)

# Step 3 - run the program
sendToKodi(createListing())
