import xbmc
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, addDirectoryItems, endOfDirectory, setResolvedUrl, setContent
from urlparse import urlparse, parse_qsl, urlsplit
from urllib import urlencode
from string import join

"""
Utility functions for xbmc

"""

def setViewMode(handle, addon, id):
    """
    Sets the view mode for list items to integer parameter id.
    Tell xbmc it is looking at a listing of episodes, before setting a particular
    view for those items.
    
    """
    if xbmc.getSkinDir() == 'skin.confluence':
        setContent(handle, 'episodes')
        xbmc.executebuiltin('Container.SetViewMode(' + id + ')')

def yoga_class_list_item(class_info):
    """
    Takes a yogaglo class information dictionary, populating and returning
    an xbmc ListItem from that information.

    """
    li = ListItem(label=class_info['title'],
                          label2=class_info['secondLabel'],
                          iconImage=class_info['coverPicUrl'])
    li.setInfo('video', {'title': class_info['title'],
                         'plot': class_info['plot'],
                         'Duration': class_info['duration'],
                         'plotoutline': class_info['secondLabel'],
                         'tagline': class_info['teacher'],
                         'genre': "Yoga"
                     })
    li.setProperty('IsPlayable', 'true')
    return li

def yoga_category_menu_list_item(item_title, item_url, item_image_url):
    """
    Returns an xbmc ListItem with an item_title, and item_url.
    An item_image_url is can be None, meaning there is no image url, return
    a default.

    """
    if item_image_url is not None:
        li = ListItem(label=item_title, iconImage=item_image_url)
        return li
    
    li = ListItem(label=item_title, iconImage="Default.png")
    return li
    
def yoga_glo_index_menu_item(title, description):
    """
    Returns an xbmc ListItem for the yogaglo plugins index page, with a title
    and description.

    """
    li = ListItem(label=title, label2=description,
                          iconImage="Default.png")
    return li

def yoga_class_play_video(rtmp_url, play_path, swf_url, xbmc_handle):
    """
    Sets an xbmc ListItem so that it can play the video associated with that selection.

    """
    li = ListItem(path=rtmp_url)
    li.setProperty('PlayPath', play_path);
    li.setProperty('SWFPlayer', swf_url);
    setResolvedUrl(xbmc_handle, True, li)

def form_plugin_url(xbmc_plugin, query):
    """
    Forms the plugin url query parameters, returning the url query string.
    
    """
    query_string = urlencode(query)
    return join((xbmc_plugin, query_string), "?")

def addDirs(handle, linkList):
    """
    Adds the listitems in linkList to build the new plugin page from selected item.
    
    """
    return addDirectoryItems(handle, linkList, len(linkList))

def eod(handle):
    """
    Sets xbmc end of Directory for the handle.
    End of the plugin pages list items.
    
    """
    return endOfDirectory(handle)

def get_yoga_glo_input_parameters(xbmc_plugin_parameters):
    """
    Gets the dicitonary of plugin parameters from the xbmc_plugin_parameters
    url string.
    
    """
    url_parts = urlsplit(xbmc_plugin_parameters)
    query_parameters = parse_qsl(url_parts.query)
    # [] tuple returns empty map
    yoga_glo_parameters = dict(query_parameters)
    return yoga_glo_parameters

