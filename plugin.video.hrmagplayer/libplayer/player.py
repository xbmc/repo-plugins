#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
from libplayer.channel import *
from libplayer.livestream import *
from libplayer.utils import *

# Get the plugin url in plugin:// notation.
__url__ = sys.argv[0]
# Get the plugin handle as an integer number.
__handle__ = int(sys.argv[1])

__context__ = None

__liveStr__ = None

def list_shows(context):
    """
    Create the list of video categories in the Kodi interface.
    :return: None
    """
    # Get video categories
    shows = context['showList']
    # Create a list for our items.
    listing = []
    # Iterate through categories
    index = 0
    # Get live now from EPG
    live_epg = None
    if context['addon'].getSetting('live-epg') == 'true':
           live_epg = getEpg(context)
    for show in shows:
        if show['active']:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=show['name'])
            list_item.setArt({"thumb": show['image']})

            is_folder = True
            if index == 0:
                is_folder = False
                list_item.setProperty("IsPlayable", "true")
                # Set live and next items
                if live_epg != None:
                    list_item.setInfo('video', {"Plot": live_epg})

            # Pass 'listing' and show index
            url = '{0}?action=listing&show={1}'.format(__url__, str(index))
            # is_folder = True means that this item opens a sub-list of lower level items.

            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))
        index += 1
    xbmcplugin.setContent(__handle__, 'videos')
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))

    xbmcplugin.endOfDirectory(__handle__)
    
def list_episodes(context, showIndex):
    episodes = context['episodes']
    # Create a list for our items.
    listing = []
    # Iterate through categories
    index = 0
    for episode in episodes:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=episode['title'])
        list_item.setArt({"thumb": episode['image']})
        if 'text' in episode:
            list_item.setInfo('video', {"Plot": episode['text']})

        url = '{0}?action=play&url={1}&episode={2}&show={3}'.format(__url__, episode['link'], encode(episode['title']), showIndex)
        is_folder = False
        list_item.setProperty("IsPlayable", "true")
        listing.append((url, list_item, is_folder))
        index += 1
    xbmcplugin.setContent(__handle__, 'videos')
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.endOfDirectory(__handle__)
    
def getEpg(context):
    live = Livestream()
    items = live.getLiveAndNext(context)
    item_live = ''
    item_next = ''
    if len(items) > 0:
        item_live = items[0]['time'] + '  ' + items[0]['head']
        if len(items) > 1:
            item_next = items[1]['time'] + '  ' + items[1]['head']
    __liveStr__ = context['addon'].getLocalizedString(30600).encode('latin-1')
    __liveStr__ += "\n\n"
    __liveStr__ += item_live
    __liveStr__ += "\n"
    __liveStr__ += item_next
    return __liveStr__
    
def playLiveStream(context, handle, loader):
        video = context['episodes'][0]['link']
        resolved_video = loader.resolveLiveUrl(context, video)
        listitem = xbmcgui.ListItem(path=resolved_video)
        listitem.setInfo('video', {'Title': 'Livestream', 'Genre': ''})
        listitem.setMimeType('application/x-mpegurl')
        xbmcplugin.setResolvedUrl(int(handle), True, listitem)
            
def dispatch(url, handle, parameter):
    parameters = extractParameters(parameter)
    action = None
    showIndex = None
    url = None
    episode = None
    if parameters != None:
        if 'action' in parameters:
            action = parameters['action']
            xbmc.log('Action: ' + action, xbmc.LOGINFO)
        if 'show' in parameters:
            showIndex = int(parameters['show'])
            xbmc.log('Show: ' + str(showIndex), xbmc.LOGDEBUG)
        if 'url' in parameters:
            url = parameters['url']
        if 'episode' in parameters:
            episode = parameters['episode']
    else:
        xbmc.log("No parameters", xbmc.LOGINFO)
        action = None   
    
    addon = xbmcaddon.Addon()
    context = ChannelContext(addon)

    if action == None:
        list_shows(context)
    elif action == 'listing':
        loader = ChannelLoader()
        loader.loadEpisodeList(context, showIndex)
        # Play live stream immediately
        if showIndex == 0:
            playLiveStream(context, handle, loader)
        else:
            list_episodes(context, showIndex)
    elif action == 'play':
        video = getVideoLink(decode(url))

        listitem = xbmcgui.ListItem(path=video)
        id = getShowId(context, showIndex)
        title = context['showList'][showIndex]['name']
        ep = decode(episode)

        listitem.setInfo('video', {'Title': title, 'Genre': ep})
        listitem.setMimeType('video/mp4')
        xbmcplugin.setResolvedUrl(int(handle), True, listitem)
