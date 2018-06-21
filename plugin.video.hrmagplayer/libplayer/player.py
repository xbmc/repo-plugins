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
    for show in shows:
        if show['active']:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=show['name'])
            list_item.setArt({"thumb": show['image']})
 
            # Create a URL for the plugin recursive callback.
            # Example: plugin://plugin.video.example/?action=listing&category=Animals
            is_folder = True
            if index == 0:
                is_folder = False
                list_item.setProperty("IsPlayable", "true")
            # Pass 'listing' and show index
            url = '{0}?action=listing&show={1}'.format(__url__, str(index))
            # is_folder = True means that this item opens a sub-list of lower level items.

            # Add our item to the listing as a 3-element tuple.
            listing.append((url, list_item, is_folder))
        index += 1
    # Add our listing to Kodi.
    # Large lists and/or slower systems benefit from adding all items at once via addDirectoryItems
    # instead of adding one by ove via addDirectoryItem.
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    #xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(__handle__)
    
def list_episodes(context, show):
    # Get video categories
    showid = context['showList']
    episodes = context['episodes']
    # Create a list for our items.
    listing = []
    # Iterate through categories
    index = 0
    for episode in episodes:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=episode['title'], thumbnailImage=episode['image'])
        list_item.setArt({"thumb": episode['image']})

        url = '{0}?action=play&url={1}&episode={2}&show={3}'.format(__url__, episode['link'], encode(episode['title']), show)
        is_folder = False
        list_item.setProperty("IsPlayable", "true")
        listing.append((url, list_item, is_folder))
        index += 1
    xbmcplugin.addDirectoryItems(__handle__, listing, len(listing))
    xbmcplugin.endOfDirectory(__handle__)
    
def playLiveStream(context, handle, loader):
        video = context['episodes'][0]['link']
        resolved_video = loader.resolveLiveUrl(context, video)
            
        """ Show episode guide with live and next show
        live = Livestream()
        items = live.getLiveAndNext(context)
        if len(items) > 0:
            text = "Live:  " + items[0]['time'] + '  ' + items[0]['head'] + "\n" + str(items[0]['sub'])
            text += "\nNext:  " + items[1]['time'] + '  ' + items[1]['head'] + "\n" + str(items[1]['sub'])
            xbmcgui.Dialog().ok('Livestream', text)
        """
        listitem = xbmcgui.ListItem(path=resolved_video)
        listitem.setInfo('video', {'Title': 'Livestream', 'Genre': ''})
        listitem.setMimeType('application/x-mpegurl')
        xbmcplugin.setResolvedUrl(int(handle), True, listitem)
            
def dispatch(url, handle, parameter):
    parameters = extractParameters(parameter)
    action = None
    show = None
    url = None
    episode = None
    if parameters != None:
        if 'action' in parameters:
            action = parameters['action']
        if 'show' in parameters:
            show = int(parameters['show'])
        if 'url' in parameters:
            url = parameters['url']
        if 'episode' in parameters:
            episode = parameters['episode']
    else:
        xbmc.log("No actions", xbmc.LOGINFO)
        action = None   
    
    addon = xbmcaddon.Addon()
    context = ChannelContext(addon)

    if action == None:
        list_shows(context)
    elif action == 'listing':
        loader = ChannelLoader()
        loader.loadEpisodeList(context, show)
        # Play live stream immediately
        if show == 0:
            playLiveStream(context, handle, loader)
        else:
            list_episodes(context, show)
    elif action == 'play':
        video = getVideoLink(decode(url))

        listitem = xbmcgui.ListItem(path=video)
        id = getShowId(context, show)
        title = context['showList'][show]['name']
        ep = decode(episode)

        listitem.setInfo('video', {'Title': title, 'Genre': ep})
        listitem.setMimeType('video/mp4')
        xbmcplugin.setResolvedUrl(int(handle), True, listitem)
