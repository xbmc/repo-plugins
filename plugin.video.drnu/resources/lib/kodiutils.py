# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Functionality that requires Kodi imports"""
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from inputstreamhelper import Helper


addon = xbmcaddon.Addon()
get_setting = addon.getSetting
set_setting = addon.setSetting
get_addon_info = addon.getAddonInfo
addon_id = get_addon_info('id')
addon_path = get_addon_info('path')
addon_name = get_addon_info('name')
addon_fanart = get_addon_info('fanart')
resources_path = Path(addon_path)/'resources'


def tr(id):
    if isinstance(id, list):
        return '\n'.join([addon.getLocalizedString(item) for item in id])
    return addon.getLocalizedString(id)


def bool_setting(name):
    return get_setting(name) == 'true'


def log(level=0, object=None):
    """Log info messages to Kodi"""
    debug_loggin = bool_setting('log.debug')
    if debug_logging:
        message = f'[{addon_id}] {message}'
        xbmc.log(message, level)


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


def show_listing(list_items, category=None, sort='unsorted', ascending=True, content=None, cache=None, selected=None):
    """Show a virtual directory in Kodi"""
    from xbmcgui import ListItem
    from addon import plugin

    set_property('container.url', 'plugin://' + addon_id() + plugin.path)
    xbmcplugin.setPluginFanart(handle=plugin.handle, image=from_unicode(addon_fanart()))

    usemenucaching = get_setting_bool('usemenucaching', default=True)
    if cache is None:
        cache = usemenucaching
    elif usemenucaching is False:
        cache = False

    if content:
        # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
        xbmcplugin.setContent(plugin.handle, content=content)

    # Jump through hoops to get a stable breadcrumbs implementation
    category_label = ''
    if category:
        if not content:
            category_label = 'VRT MAX / '
        if plugin.path.startswith(('/favorites/', '/resumepoints/')):
            category_label += localize(30428) + ' / '  # My
        if isinstance(category, int):
            category_label += localize(category)
        else:
            category_label += category
    elif not content:
        category_label = 'VRT MAX'
    xbmcplugin.setPluginCategory(handle=plugin.handle, category=category_label)

    # FIXME: Since there is no way to influence descending order, we force it here
    if not ascending:
        sort = 'unsorted'

    # NOTE: When showing tvshow listings and 'showoneoff' was set, force 'unsorted'
    if get_setting_bool('showoneoff', default=True) and sort == 'label' and content == 'tvshows':
        sort = 'unsorted'

    # Add all sort methods to GUI (start with preferred)
    xbmcplugin.addSortMethod(handle=plugin.handle, sortMethod=SORT_METHODS[sort])
    for key in sorted(SORT_METHODS):
        if key != sort:
            xbmcplugin.addSortMethod(handle=plugin.handle, sortMethod=SORT_METHODS[key])

    # FIXME: This does not appear to be working, we have to order it ourselves
#    xbmcplugin.setProperty(handle=plugin.handle, key='sort.ascending', value='true' if ascending else 'false')
#    if ascending:
#        xbmcplugin.setProperty(handle=plugin.handle, key='sort.order', value=str(SORT_METHODS[sort]))
#    else:
#        # NOTE: When descending, use unsorted
#        xbmcplugin.setProperty(handle=plugin.handle, key='sort.order', value=str(SORT_METHODS['unsorted']))

    listing = []
    showfanart = get_setting_bool('showfanart', default=True)
    for title_item in list_items:
        # Three options:
        #  - item is a virtual directory/folder (not playable, path)
        #  - item is a playable file (playable, path)
        #  - item is non-actionable item (not playable, no path)
        is_folder = bool(not title_item.is_playable and title_item.path)
        is_playable = bool(title_item.is_playable and title_item.path)

        list_item = ListItem(label=title_item.label)

        prop_dict = {
            'IsInternetStream': 'true' if is_playable else 'false',
            'IsPlayable': 'true' if is_playable else 'false',
            'IsFolder': 'false' if is_folder else 'true',
        }
        if title_item.prop_dict:
            title_item.prop_dict.update(prop_dict)
        else:
            title_item.prop_dict = prop_dict
        # NOTE: The setProperties method is new in Kodi18
        try:
            list_item.setProperties(title_item.prop_dict)
        except AttributeError:
            for key, value in list(title_item.prop_dict.items()):
                list_item.setProperty(key=key, value=str(value))

        # FIXME: The setIsFolder method is new in Kodi18, so we cannot use it just yet
        # list_item.setIsFolder(is_folder)

        if showfanart:
            # Add add-on fanart when fanart is missing
            if not title_item.art_dict:
                title_item.art_dict = {'fanart': addon_fanart()}
            elif not title_item.art_dict.get('fanart'):
                title_item.art_dict.update(fanart=addon_fanart())
            list_item.setArt(title_item.art_dict)

        if title_item.info_dict:
            # type is one of: video, music, pictures, game
            list_item.setInfo(type='video', infoLabels=title_item.info_dict)

        if title_item.stream_dict:
            # type is one of: video, audio, subtitle
            list_item.addStreamInfo('video', title_item.stream_dict)

        if title_item.context_menu:
            list_item.addContextMenuItems(title_item.context_menu)

        url = None
        if title_item.path:
            url = title_item.path

        listing.append((url, list_item, is_folder))

    # Jump to specific item
    if selected is not None:
        pass
#        from xbmcgui import getCurrentWindowId, Window
#        wnd = Window(getCurrentWindowId())
#        wnd.getControl(wnd.getFocusId()).selectItem(selected)

    succeeded = xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle, succeeded, updateListing=False, cacheToDisc=cache)


def get_property(key, default=None, window_id=10000):
    """Get a Window property"""
    from xbmcgui import Window
    value = to_unicode(Window(window_id).getProperty(key))
    if value == '' and default is not None:
        return default
    return value


def set_property(key, value, window_id=10000):
    """Set a Window property"""
    from xbmcgui import Window
    return Window(window_id).setProperty(key, from_unicode(value))


def clear_property(key, window_id=10000):
    """Clear a Window property"""
    from xbmcgui import Window
    return Window(window_id).clearProperty(key)


def end_of_directory():
    """Close a virtual directory, required to avoid a waiting Kodi"""
    from addon import plugin
    xbmcplugin.endOfDirectory(handle=plugin.handle, succeeded=False, updateListing=False, cacheToDisc=False)


def current_container_url():
    """Get current container plugin:// url"""
    url = xbmc.getInfoLabel('Container.FolderPath')
    if url == '':
        return None
    return url


def container_refresh(url=None):
    """Refresh the current container or (re)load a container by URL"""
    if url:
        log(3, f'Execute: Container.Refresh({url})')
        xbmc.executebuiltin(f'Container.Refresh({url})')
    else:
        log(3, 'Execute: Container.Refresh')
        xbmc.executebuiltin('Container.Refresh')


def container_update(url):
    """Update the current container while respecting the path history."""
    if url:
        log(3, f'Execute: Container.Update({url})')
        xbmc.executebuiltin(f'Container.Update({url})')
    else:
        # URL is a mandatory argument for Container.Update, use Container.Refresh instead
        container_refresh()


def container_reload(url=None):
    """Only update container if the play action was initiated from it"""
    if url is None:
        url = get_property('container.url')
    if current_container_url() != url:
        return
    container_update(url)
