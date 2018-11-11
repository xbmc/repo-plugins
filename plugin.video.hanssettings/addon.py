'''
    Hans Settings
    ~~~~~~~

    An XBMC addon for watching hanssettings 
    :license: GPLv3, see LICENSE.txt for more details.
    
'''
import sys
if (sys.version_info[0] == 3):
    # For Python 3.0 and later
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl
else:
    # Fall back to Python 2's urllib2
    from urllib import urlencode
    from urlparse import parse_qsl

import resources.lib.hanssettings
import time
import xbmcplugin, xbmcgui, xbmcaddon

PLUGIN_NAME = 'hanssettings'
PLUGIN_ID = 'plugin.video.hanssettings'

_hanssettings = resources.lib.hanssettings.HansSettings()
_url = sys.argv[0]
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()

# In deze file heb ik alle logica van kodi zitten.
# hier worden alle files ook gecached, want dat is een kodi addon.

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.
    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_categories():
    githubfiles = _hanssettings.get_dataoverzicht()
    return _hanssettings.get_overzicht(githubfiles)

def get_videos(streamfile):
    streamsdatafile = _hanssettings.get_datafromfilegithub(streamfile)
    return _hanssettings.get_items(streamsdatafile)

def list_categories():
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(32004))
    xbmcplugin.setContent(_handle, 'videos')
    i = 0
    categories = get_categories()
    categoriesLength = len(categories)
    progress = xbmcgui.DialogProgress()
    progress.create(_addon.getLocalizedString(32002), _addon.getLocalizedString(32001))
    for category in categories:
        i = i + 1
        progressText = _addon.getLocalizedString(32003) % (i, categoriesLength)
        progress.update( 100 / categoriesLength * i, "", progressText)
        if progress.iscanceled():
            break
        datafile = _hanssettings.get_datafromfilegithub(category)
        list_item = xbmcgui.ListItem(label=_hanssettings.get_name(datafile, category))
        list_item.setInfo('video', {'title': _hanssettings.get_name(datafile, category),
                                    'mediatype': 'video'})
        url = get_url(action='listing', category=category)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    progress.close()
    del progress
    xbmcplugin.endOfDirectory(_handle)

def add_playable_listitem(video):
    list_item = xbmcgui.ListItem(label=video['label'])
    list_item.setInfo('video', {'title': video['label'],
                'mediatype': 'video'})
    list_item.setProperty('IsPlayable', 'true')
    url = get_url(action='play', video=video['stream'])
    is_folder = False
    xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

def list_videos_and_subfolder(category):
    datafile = _hanssettings.get_datafromfilegithub(category)
    xbmcplugin.setPluginCategory(_handle, _hanssettings.get_name(datafile, category))
    xbmcplugin.setContent(_handle, 'videos')
    for item in get_videos(category):
        if (item['subfolder']):
            list_item = xbmcgui.ListItem(label=item['label'])
            list_item.setInfo('video', {'title': item['label'],
                            'mediatype': 'video'})
            url = get_url(action='subfolder', category=category, counter=item['counter'])
            is_folder = True
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
        else:
            for stream in item['streams']:
                add_playable_listitem(stream)
    xbmcplugin.endOfDirectory(_handle)

def list_subfolder(category, counter):
    datafile = _hanssettings.get_datafromfilegithub(category)
    item = _hanssettings.get_items_subfolder(datafile, counter)
    xbmcplugin.setPluginCategory(_handle, item['label'])
    xbmcplugin.setContent(_handle, 'videos')
    for stream in item['streams']:
        add_playable_listitem(stream)
    xbmcplugin.endOfDirectory(_handle)

def play_video(path):
    if (path.find('?#User-Agent') > -1):
        path = path.partition('?#User-Agent')[0] + '|User-Agent'+path.partition('?#User-Agent')[2]
    xbmc.log('path: ' + path, xbmc.LOGDEBUG)
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

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
            list_videos_and_subfolder(params['category'])
        elif params['action'] == 'subfolder':
            list_subfolder(params['category'], params['counter'])
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
