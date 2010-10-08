# Copyright 2010 by peterpanzki

import sys
import xbmcgui, xbmcplugin
import feedparser,re
 
def addLinkItem(url,li):
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
    
def show_new_vids_submenu():
    # List New Videos 
    feeds = feedparser.parse("http://rss.kicker.de/media/videos")
    for feed in feeds.entries:
        liStyle=xbmcgui.ListItem(feed.title, iconImage="default.png", thumbnailImage=feed.enclosures[0].href)
        vnr = (re.compile(r'/\d+/').findall(feed.link)[0]).strip('/')
        url = "http://video.kicker.de/flash/" + vnr + "_560x315_VP6_576.flv"
        liStyle.setInfo( type="Video", infoLabels={ "Title": feed.title, "plot": feed.summary })
        addLinkItem(url, liStyle)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
 
show_new_vids_submenu()