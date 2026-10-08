#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Common Kodi-specific utilities for the DRNU addon"""

__all__ = [
    # Addon instance accessors
    'get_addon', 'get_setting', 'set_setting', 'get_addon_info', 'resources_path',
    # Utility functions
    'tr', 'bool_setting', 'log',
    'kodi_version', 'kodi_version_major', 'version',
    # Kodi UI and plugin utilities
    'get_plugin_handle', 'end_of_directory', 'set_plugin_content',
    'set_plugin_category', 'set_plugin_fanart', 'add_directory_items',
    'add_sort_method', 'container_refresh', 'container_update',
    'get_current_container_url',
    # Window properties
    'get_window_property', 'set_window_property', 'clear_window_property',
    # Dialogs
    'show_ok_dialog', 'show_yesno_dialog', 'get_keyboard_input',
    # Built-in commands
    'execute_builtin',
]

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

# The addon instance is created on first use, not at import time, so that
# importing kodiutils does not require a Kodi environment.
_addon = None


def get_addon():
    """Return the xbmcaddon.Addon() instance, creating it on first use."""
    global _addon
    if _addon is None:
        _addon = xbmcaddon.Addon()
    return _addon


def get_setting(name):
    """Get a setting value as string"""
    return get_addon().getSetting(name)


def set_setting(name, value):
    """Set a setting value"""
    get_addon().setSetting(name, value)


def get_addon_info(key):
    """Get addon metadata (id, path, version, ...)"""
    return get_addon().getAddonInfo(key)


def resources_path():
    """Path to the addon's resources directory (lazy: needs get_addon_info)"""
    from pathlib import Path
    return Path(get_addon_info('path')) / 'resources'


def tr(id):
    """Get localized string from addon strings.po

    Args:
        id: String ID (int) or list of string IDs

    Returns:
        Localized string, or multiple strings joined by newlines if id is a list
    """
    if isinstance(id, list):
        return '\n'.join([get_addon().getLocalizedString(item) for item in id])
    return get_addon().getLocalizedString(id)


def bool_setting(name, default=False):
    """Get a setting as a boolean value

    Args:
        name: Setting name
        default: Default value if setting is not 'true' (default: False)

    Returns:
        True if setting equals 'true', False otherwise
    """
    return get_setting(name) == 'true'


def log(object, level=0):
    """Log a message to Kodi debug log if debug logging is enabled

    Args:
        object: The object to log (will be converted to string)
        level: Log level (default: 0 = xbmc.LOGDEBUG)
    """
    if bool_setting('log.debug'):
        xbmc.log(str(object), level)


def kodi_version():
    """Get full Kodi version as string (e.g., '20.2')"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Get major Kodi version as integer (e.g., 20 for Kodi 20.x)"""
    return int(kodi_version().split('.')[0])


def version(s):
    """Parse a version string into a list of integers

    Args:
        s: Version string (e.g., '6.2.0' or '6.2.0+build123')

    Returns:
        List of integers (e.g., [6, 2, 0])
    """
    return [int(item) for item in s.split('-')[0].split('.')]


def get_plugin_handle():
    """Get the current plugin handle from xbmcplugin"""
    return xbmcplugin.getHandle()


def end_of_directory(handle=None, succeeded=False, update_listing=False, cache_to_disc=False):
    """End a virtual directory listing

    Args:
        handle: Plugin handle (defaults to current handle)
        succeeded: Whether directory items were added successfully
        update_listing: Whether to update the listing
        cache_to_disc: Whether to cache the listing to disc
    """
    if handle is None:
        handle = get_plugin_handle()
    xbmcplugin.endOfDirectory(
        handle=handle,
        succeeded=succeeded,
        updateListing=update_listing,
        cacheToDisc=cache_to_disc
    )


def set_plugin_content(handle, content_type):
    """Set the content type for a plugin directory

    Args:
        handle: Plugin handle
        content_type: Content type string (e.g., 'episodes', 'movies', 'tvshows')
    """
    xbmcplugin.setContent(handle, content_type)


def set_plugin_category(handle, category):
    """Set the category for a plugin directory

    Args:
        handle: Plugin handle
        category: Category string to display
    """
    xbmcplugin.setPluginCategory(handle, category)


def set_plugin_fanart(handle, image_path):
    """Set fanart for a plugin directory

    Args:
        handle: Plugin handle
        image_path: Path to fanart image
    """
    xbmcplugin.setPluginFanart(handle, image_path)


def add_directory_items(handle, items, total_items=None):
    """Add directory items to a plugin listing

    Args:
        handle: Plugin handle
        items: List of (url, list_item, is_folder) tuples
        total_items: Total number of items (for progress indication)

    Returns:
        True if items were added successfully
    """
    return xbmcplugin.addDirectoryItems(handle, items, total_items)


def add_sort_method(handle, sort_method, label2=None):
    """Add a sort method to a plugin directory

    Args:
        handle: Plugin handle
        sort_method: Sort method constant (e.g., xbmcplugin.SORT_METHOD_LABEL)
        label2: Optional secondary sort label
    """
    if label2 is not None:
        xbmcplugin.addSortMethod(handle, sort_method, label2)
    else:
        xbmcplugin.addSortMethod(handle, sort_method)


def container_refresh(url=None):
    """Refresh the current container or a specific URL

    Args:
        url: Optional URL to refresh (defaults to current container)
    """
    if url:
        log(3, f'Execute: Container.Refresh({url})')
        xbmc.executebuiltin(f'Container.Refresh({url})')
    else:
        log(3, 'Execute: Container.Refresh')
        xbmc.executebuiltin('Container.Refresh')


def container_update(url):
    """Update the current container while respecting path history

    Args:
        url: URL to update
    """
    if url:
        log(3, f'Execute: Container.Update({url})')
        xbmc.executebuiltin(f'Container.Update({url})')
    else:
        container_refresh()


def get_current_container_url():
    """Get the current container plugin:// URL

    Returns:
        Current container URL as string, or None if not available
    """
    url = xbmc.getInfoLabel('Container.FolderPath')
    if url == '':
        return None
    return url


def get_window_property(key, default=None, window_id=10000):
    """Get a window property value

    Args:
        key: Property key
        default: Default value if property is empty
        window_id: Window ID (default: 10000 = home window)

    Returns:
        Property value as string, or default if empty
    """
    from xbmcgui import Window
    value = Window(window_id).getProperty(key)
    if value == '' and default is not None:
        return default
    return value


def set_window_property(key, value, window_id=10000):
    """Set a window property value

    Args:
        key: Property key
        value: Property value
        window_id: Window ID (default: 10000 = home window)
    """
    from xbmcgui import Window
    Window(window_id).setProperty(key, str(value))


def clear_window_property(key, window_id=10000):
    """Clear a window property

    Args:
        key: Property key
        window_id: Window ID (default: 10000 = home window)
    """
    from xbmcgui import Window
    Window(window_id).clearProperty(key)


def show_ok_dialog(title, message, autoclose=False):
    """Show an OK dialog

    Args:
        title: Dialog title
        message: Dialog message
        autoclose: If True, dialog auto-closes after a timeout
    """
    dialog = xbmcgui.Dialog()
    if autoclose:
        dialog.ok(title, message, '', '')
    else:
        dialog.ok(title, message)


def show_yesno_dialog(title, message, yeslabel=None, nolabel=None, autoclose=False):
    """Show a yes/no dialog

    Args:
        title: Dialog title
        message: Dialog message
        yeslabel: Custom yes label (default: localized Yes)
        nolabel: Custom no label (default: localized No)
        autoclose: If True, dialog auto-closes after a timeout

    Returns:
        True if Yes was selected, False if No
    """
    dialog = xbmcgui.Dialog()
    return dialog.yesno(title, message, yeslabel=yeslabel, nolabel=nolabel, autoclose=autoclose)


def get_keyboard_input(title, default='', hidden=False):
    """Show a keyboard dialog for user input

    Args:
        title: Dialog title
        default: Default text (default: '')
        hidden: If True, input is hidden (for passwords)

    Returns:
        User input string if confirmed, None otherwise
    """
    keyboard = xbmc.Keyboard(default, title, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    return None


def execute_builtin(command):
    """Execute a Kodi built-in command

    Args:
        command: Built-in command string
    """
    xbmc.executebuiltin(command)
