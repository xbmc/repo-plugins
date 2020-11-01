# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""All functionality that requires Kodi imports"""

from __future__ import absolute_import, division, unicode_literals
import logging

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon()

SORT_METHODS = dict(
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
    label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS,
    title=xbmcplugin.SORT_METHOD_TITLE,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    year=xbmcplugin.SORT_METHOD_VIDEO_YEAR,
    date=xbmcplugin.SORT_METHOD_DATE,
)
DEFAULT_SORT_METHODS = [
    'unsorted', 'title'
]

_LOGGER = logging.getLogger('kodiutils')


class TitleItem:
    """ This helper object holds all information to be used with Kodi xbmc's ListItem object """

    def __init__(self, title, path=None, art_dict=None, info_dict=None, prop_dict=None, stream_dict=None,
                 context_menu=None, subtitles_path=None,
                 is_playable=False):
        """ The constructor for the TitleItem class.

        :param str title:
        :param str path:
        :param dict art_dict:
        :param dict info_dict:
        :param dict prop_dict:
        :param dict stream_dict:
        :param list[tuple[str, str]] context_menu:
        :param list[str] subtitles_path:
        :param bool is_playable:
        """
        self.title = title
        self.path = path
        self.art_dict = art_dict
        self.info_dict = info_dict
        self.stream_dict = stream_dict
        self.prop_dict = prop_dict
        self.context_menu = context_menu
        self.subtitles_path = subtitles_path
        self.is_playable = is_playable

    def __repr__(self):
        return "%r" % self.__dict__


class SafeDict(dict):
    """A safe dictionary implementation that does not break down on missing keys"""

    def __missing__(self, key):
        """Replace missing keys with the original placeholder"""
        return '{' + key + '}'


def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text


def from_unicode(text, encoding='utf-8', errors='strict'):
    """Force unicode to text"""
    import sys
    if sys.version_info.major == 2 and isinstance(text, unicode):  # noqa: F821; pylint: disable=undefined-variable
        return text.encode(encoding, errors)
    return text


def addon_fanart():
    """Return add-on fanart"""
    return get_addon_info('fanart')


def addon_icon():
    """Return add-on icon"""
    return get_addon_info('icon')


def addon_id():
    """Return add-on ID"""
    return get_addon_info('id')


def addon_name():
    """Cache and return add-on name"""
    return get_addon_info('name')


def addon_path():
    """Cache and return add-on path"""
    return get_addon_info('path')


def addon_profile():
    """Cache and return add-on profile"""
    return to_unicode(xbmc.translatePath(ADDON.getAddonInfo('profile')))


def url_for(name, *args, **kwargs):
    """Wrapper for plugin.url_for() to lookup by name"""
    import addon
    return addon.plugin.url_for(getattr(addon, name), *args, **kwargs)


def show_listing(title_items, category=None, sort=None, content=None, cache=True):
    """Show a virtual directory in Kodi"""
    from addon import plugin

    if content:
        # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos, videos, images, games
        xbmcplugin.setContent(plugin.handle, content=content)

    # Jump through hoops to get a stable breadcrumbs implementation
    category_label = ''
    if category:
        if not content:
            category_label = addon_name() + ' / '
        if isinstance(category, int):
            category_label += localize(category)
        else:
            category_label += category
    elif not content:
        category_label = addon_name()

    xbmcplugin.setPluginCategory(handle=plugin.handle, category=category_label)

    # Add all sort methods to GUI (start with preferred)
    if sort is None:
        sort = DEFAULT_SORT_METHODS
    elif not isinstance(sort, list):
        sort = [sort] + DEFAULT_SORT_METHODS

    for key in sort:
        xbmcplugin.addSortMethod(handle=plugin.handle, sortMethod=SORT_METHODS[key])

    # Add the listings
    listing = []
    for title_item in title_items:
        # Three options:
        #  - item is a virtual directory/folder (not playable, path)
        #  - item is a playable file (playable, path)
        #  - item is non-actionable item (not playable, no path)
        is_folder = bool(not title_item.is_playable and title_item.path)
        is_playable = bool(title_item.is_playable and title_item.path)

        list_item = xbmcgui.ListItem(label=title_item.title, path=title_item.path)

        if title_item.prop_dict:
            list_item.setProperties(title_item.prop_dict)
        list_item.setProperty(key='IsPlayable', value='true' if is_playable else 'false')

        list_item.setIsFolder(is_folder)

        if title_item.art_dict:
            list_item.setArt(title_item.art_dict)

        if title_item.info_dict:
            # type is one of: video, music, pictures, game
            list_item.setInfo(type='video', infoLabels=title_item.info_dict)

        if title_item.stream_dict:
            # type is one of: video, audio, subtitle
            list_item.addStreamInfo('video', title_item.stream_dict)

        if title_item.context_menu:
            list_item.addContextMenuItems(title_item.context_menu)

        is_folder = bool(not title_item.is_playable and title_item.path)
        url = title_item.path if title_item.path else None
        listing.append((url, list_item, is_folder))

    succeeded = xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle, succeeded, cacheToDisc=cache)


def play(stream, title=None, art_dict=None, info_dict=None, prop_dict=None):
    """Play the given stream"""
    from addon import plugin

    play_item = xbmcgui.ListItem(label=title, path=stream)
    if art_dict:
        play_item.setArt(art_dict)
    if info_dict:
        play_item.setInfo(type='video', infoLabels=info_dict)
    if prop_dict:
        play_item.setProperties(prop_dict)

    # Setup Inputstream Adaptive
    if kodi_version_major() >= 19:
        play_item.setProperty('inputstream', 'inputstream.adaptive')
    else:
        play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
    # play_item.setMimeType('application/dash+xml')
    play_item.setContentLookup(False)

    xbmcplugin.setResolvedUrl(plugin.handle, True, listitem=play_item)


def get_search_string(heading='', message=''):
    """Ask the user for a search string"""
    search_string = None
    keyboard = xbmc.Keyboard(message, heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())
    return search_string


def ok_dialog(heading='', message=''):
    """Show Kodi's OK dialog"""
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    if kodi_version_major() < 19:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        return Dialog().ok(heading=heading, line1=message)
    return Dialog().ok(heading=heading, message=message)


def localize(string_id, **kwargs):
    """Return the translated string from the .po language files, optionally translating variables"""
    if kwargs:
        from string import Formatter
        return Formatter().vformat(ADDON.getLocalizedString(string_id), (), SafeDict(**kwargs))
    return ADDON.getLocalizedString(string_id)


def get_setting(key, default=None):
    """Get an add-on setting as string"""
    try:
        value = to_unicode(ADDON.getSetting(key))
    except RuntimeError:  # Occurs when the add-on is disabled
        return default
    if value == '' and default is not None:
        return default
    return value


def get_cond_visibility(condition):
    """Test a condition in XBMC"""
    return xbmc.getCondVisibility(condition)


def has_addon(name):
    """Checks if add-on is installed"""
    return get_cond_visibility('System.HasAddon(%s)' % name) == 1


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


def get_addon_info(key):
    """Return addon information"""
    return to_unicode(ADDON.getAddonInfo(key))
