'''
    Uitzendinggemist(NPO)
    ~~~~~~~

    An XBMC addon for watching uzg 
    :license: GPLv3, see LICENSE.txt for more details.
    
    based on: https://github.com/jbeluch/plugin.video.documentary.net
    Uitzendinggemist(NPO) / uzg = Made by Bas Magre (Opvolger)
    
'''
import resources.lib.uzg

import sys
try:
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib import urlencode
    from urlparse import parse_qsl

import time
import xbmcplugin, xbmcgui

PLUGIN_NAME = 'uzg'
PLUGIN_ID = 'plugin.video.uzg'

uzg = resources.lib.uzg.Uzg()

_url = sys.argv[0]
_handle = int(sys.argv[1])

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def setMediaView():
    try:
        kodiVersion = xbmc.getInfoLabel('System.BuildVersion').split()[0]
        kodiVersion = kodiVersion.split('.')[0]
        skinTheme = xbmc.getSkinDir().lower()
        if 'onfluence' in skinTheme:
            xbmc.executebuiltin('Container.SetViewMode(504)')
    except:
        pass 

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Uitzendinggemist (NPO)')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get video categories
    categories = uzg.get_overzicht()
    # Iterate through categories
    for category in categories:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=category['label'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': category['thumbnail'],
                           'icon':  category['thumbnail'],
                           'fanart':  category['thumbnail']})
        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': category['label'],
                                    'plot': category['plot'],
                                    'genre': category['genres'],
                                    'studio': category['studio'],
                                    'mediatype': 'video'})
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&category=Animals
        url = get_url(action='listing', nebo_id=category['nebo_id'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def list_videos(nebo_id):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, nebo_id)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')
    # Get the list of videos in the category.
    videos = uzg.get_items(nebo_id)
    # Iterate through videos.
    for video in videos:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['label'])
        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {'title': video['label'],
                                     'date': video['date'],
                                     'premiered': video['premiered'],
                                     'aired': video['aired'],
                                     'plot': video['plot'],
                                     'studio': video['studio'],
                                     'year': video['year'],
                                     'duration': video['duration'],
                                     'genre': video['genres'],
                                    'mediatype': 'video'})
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({'thumb': video['thumbnail'], 'icon': video['thumbnail'], 'fanart': video['thumbnail']})
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(action='play', whatson_id=video['whatson_id'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def play_video(whatson_id):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :type path: str
    """
    play_item = xbmcgui.ListItem(path=uzg.get_play_url(whatson_id))
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    if (xbmcplugin.getSetting(_handle, "subtitle") == 'true'):
    	add_subtitlesstream(uzg.get_ondertitel(whatson_id))

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params['nebo_id'])
            setMediaView()
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['whatson_id'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()
        setMediaView()

def add_subtitlesstream(subtitles):
	player = xbmc.Player()
	for _ in range(30):
		if player.isPlaying():
			break
		time.sleep(1)
	else:
		raise Exception('No video playing. Aborted after 30 seconds.')
	player.setSubtitles(subtitles)
	player.setSubtitleStream(1)

if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
