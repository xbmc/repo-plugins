# -*- coding: utf-8 -*-
"""All functionality that requires Kodi imports"""

from __future__ import absolute_import, division, unicode_literals

import logging
import os

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

_LOGGER = logging.getLogger(__name__)


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


def addon_icon():
    """Cache and return add-on icon"""
    return get_addon_info('icon')


def addon_id():
    """Cache and return add-on ID"""
    return get_addon_info('id')


def addon_fanart():
    """Cache and return add-on fanart"""
    return get_addon_info('fanart')


def addon_name():
    """Cache and return add-on name"""
    return get_addon_info('name')


def addon_path():
    """Cache and return add-on path"""
    return get_addon_info('path')


def translate_path(path):
    """Converts a Kodi special:// path to a normal path"""
    try:  # Kodi 19 alpha 2 and higher
        from xbmcvfs import translatePath
    except ImportError:  # Kodi 19 alpha 1 and lower
        return to_unicode(xbmc.translatePath(from_unicode(path)))
    return translatePath(path)


def addon_profile():
    """Cache and return add-on profile"""
    return translate_path(ADDON.getAddonInfo('profile'))


def url_for(name, *args, **kwargs):
    """Wrapper for routing.url_for() to lookup by name"""
    import resources.lib.addon as addon
    return addon.routing.url_for(getattr(addon, name), *args, **kwargs)


def show_listing(title_items, category=None, sort=None, content=None, cache=True):
    """Show a virtual directory in Kodi"""
    from resources.lib.addon import routing

    if content:
        # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos, videos, images, games
        xbmcplugin.setContent(routing.handle, content=content)

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

    xbmcplugin.setPluginCategory(handle=routing.handle, category=category_label)

    # Add all sort methods to GUI (start with preferred)
    if sort is None:
        sort = DEFAULT_SORT_METHODS
    elif not isinstance(sort, list):
        sort = [sort] + DEFAULT_SORT_METHODS

    for key in sort:
        xbmcplugin.addSortMethod(handle=routing.handle, sortMethod=SORT_METHODS[key])

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

    succeeded = xbmcplugin.addDirectoryItems(routing.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(routing.handle, succeeded, cacheToDisc=cache)


def play(stream, license_key=None, title=None, art_dict=None, info_dict=None, prop_dict=None):
    """Play the given stream"""
    from resources.lib.addon import routing

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
    play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    play_item.setMimeType('application/dash+xml')
    play_item.setContentLookup(False)

    if license_key is not None:
        import inputstreamhelper
        is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
        if is_helper.check_inputstream():
            play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            play_item.setProperty('inputstream.adaptive.license_key', license_key)

    xbmcplugin.setResolvedUrl(routing.handle, True, listitem=play_item)


def get_search_string(heading='', message=''):
    """Ask the user for a search string"""
    search_string = None
    keyboard = xbmc.Keyboard(message, heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_string = to_unicode(keyboard.getText())
    return search_string.strip()


def get_numeric_input(heading='', default=''):
    """Ask the user for a numeric input."""
    value = xbmcgui.Dialog().numeric(0, heading, default)
    return value


def ok_dialog(heading='', message=''):
    """Show Kodi's OK dialog"""
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    if kodi_version_major() < 19:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        return Dialog().ok(heading=heading, line1=message)
    return Dialog().ok(heading=heading, message=message)


def yesno_dialog(heading='', message='', nolabel=None, yeslabel=None, autoclose=0):
    """Show Kodi's Yes/No dialog"""
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    if kodi_version_major() < 19:
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        return Dialog().yesno(heading=heading, line1=message, nolabel=nolabel, yeslabel=yeslabel,
                              autoclose=autoclose)
    return Dialog().yesno(heading=heading, message=message, nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)


def notification(heading='', message='', icon='info', time=4000):
    """Show a Kodi notification"""
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    if not icon:
        icon = addon_icon()
    Dialog().notification(heading=heading, message=message, icon=icon, time=time)


def multiselect(heading='', options=None, autoclose=0, preselect=None, use_details=False):
    """Show a Kodi multi-select dialog"""
    from xbmcgui import Dialog
    if not heading:
        heading = addon_name()
    return Dialog().multiselect(heading=heading, options=options, autoclose=autoclose, preselect=preselect,
                                useDetails=use_details)


class progress(xbmcgui.DialogProgress, object):  # pylint: disable=invalid-name,useless-object-inheritance
    """Show Kodi's Progress dialog"""

    def __init__(self, heading='', message=''):
        """Initialize and create a progress dialog"""
        super(progress, self).__init__()
        if not heading:
            heading = ADDON.getAddonInfo('name')
        self.create(heading, message=message)

    def create(self, heading, message=''):  # pylint: disable=arguments-differ
        """Create and show a progress dialog"""
        if kodi_version_major() < 19:
            lines = message.split('\n', 2)
            line1, line2, line3 = (lines + [None] * (3 - len(lines)))
            # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            return super(progress, self).create(heading, line1=line1, line2=line2, line3=line3)
        return super(progress, self).create(heading, message=message)

    def update(self, percent, message=''):  # pylint: disable=arguments-differ
        """Update the progress dialog"""
        if kodi_version_major() < 19:
            lines = message.split('\n', 2)
            line1, line2, line3 = (lines + [None] * (3 - len(lines)))
            # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            return super(progress, self).update(percent, line1=line1, line2=line2, line3=line3)
        return super(progress, self).update(percent, message=message)


def set_locale():
    """Load the proper locale for date strings, only once"""
    if hasattr(set_locale, 'cached'):
        return getattr(set_locale, 'cached')
    from locale import Error, LC_ALL, setlocale
    locale_lang = get_global_setting('locale.language').split('.')[-1]
    locale_lang = locale_lang[:-2] + locale_lang[-2:].upper()
    # NOTE: setlocale() only works if the platform supports the Kodi configured locale
    try:
        setlocale(LC_ALL, locale_lang)
    except (Error, ValueError) as exc:
        if locale_lang != 'en_GB':
            _LOGGER.debug("Your system does not support locale '%s': %s", locale_lang, exc)
            set_locale.cached = False
            return False
    set_locale.cached = True
    return True


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


def get_setting_bool(key, default=None):
    """Get an add-on setting as boolean"""
    try:
        return ADDON.getSettingBool(key)
    except (AttributeError, TypeError):  # On Krypton or older, or when not a boolean
        value = get_setting(key, default)
        if value not in ('false', 'true'):
            return default
        return bool(value == 'true')
    except RuntimeError:  # Occurs when the add-on is disabled
        return default


def get_setting_int(key, default=None):
    """Get an add-on setting as integer"""
    try:
        return ADDON.getSettingInt(key)
    except (AttributeError, TypeError):  # On Krypton or older, or when not an integer
        value = get_setting(key, default)
        try:
            return int(value)
        except ValueError:
            return default
    except RuntimeError:  # Occurs when the add-on is disabled
        return default


def get_setting_float(key, default=None):
    """Get an add-on setting"""
    try:
        return ADDON.getSettingNumber(key)
    except (AttributeError, TypeError):  # On Krypton or older, or when not a float
        value = get_setting(key, default)
        try:
            return float(value)
        except ValueError:
            return default
    except RuntimeError:  # Occurs when the add-on is disabled
        return default


def set_setting(key, value):
    """Set an add-on setting"""
    return ADDON.setSetting(key, from_unicode(str(value)))


def set_setting_bool(key, value):
    """Set an add-on setting as boolean"""
    try:
        return ADDON.setSettingBool(key, value)
    except (AttributeError, TypeError):  # On Krypton or older, or when not a boolean
        if value in ['false', 'true']:
            return set_setting(key, value)
        if value:
            return set_setting(key, 'true')
        return set_setting(key, 'false')


def set_setting_int(key, value):
    """Set an add-on setting as integer"""
    try:
        return ADDON.setSettingInt(key, value)
    except (AttributeError, TypeError):  # On Krypton or older, or when not an integer
        return set_setting(key, value)


def set_setting_float(key, value):
    """Set an add-on setting"""
    try:
        return ADDON.setSettingNumber(key, value)
    except (AttributeError, TypeError):  # On Krypton or older, or when not a float
        return set_setting(key, value)


def open_settings():
    """Open the add-in settings window, shows Credentials"""
    ADDON.openSettings()


def get_global_setting(key):
    """Get a Kodi setting"""
    result = jsonrpc(method='Settings.GetSettingValue', params=dict(setting=key))
    return result.get('result', {}).get('value')


def set_global_setting(key, value):
    """Set a Kodi setting"""
    return jsonrpc(method='Settings.SetSettingValue', params=dict(setting=key, value=value))


def get_cond_visibility(condition):
    """Test a condition in XBMC"""
    return xbmc.getCondVisibility(condition)


def has_addon(name):
    """Checks if add-on is installed"""
    return xbmc.getCondVisibility('System.HasAddon(%s)' % name) == 1


def has_credentials():
    """Whether the add-on has credentials filled in"""
    return bool(get_setting('username') and get_setting('password'))


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


def get_tokens_path():
    """Cache and return the userdata tokens path"""
    if not hasattr(get_tokens_path, 'cached'):
        get_tokens_path.cached = os.path.join(addon_profile(), 'tokens')
    return getattr(get_tokens_path, 'cached')


def get_cache_path():
    """Cache and return the userdata cache path"""
    if not hasattr(get_cache_path, 'cached'):
        get_cache_path.cached = os.path.join(addon_profile(), 'cache')
    return getattr(get_cache_path, 'cached')


def get_addon_info(key):
    """Return addon information"""
    return to_unicode(ADDON.getAddonInfo(key))


def execute_builtin(function):
    """ Execute a Kodi Builtin """
    xbmc.executebuiltin(function)


def container_refresh(url=None):
    """Refresh the current container or (re)load a container by URL"""
    if url:
        _LOGGER.debug('Execute: Container.Refresh(%s)', url)
        xbmc.executebuiltin('Container.Refresh({url})'.format(url=url))
    else:
        _LOGGER.debug('Execute: Container.Refresh')
        xbmc.executebuiltin('Container.Refresh')


def container_update(url):
    """Update the current container while respecting the path history."""
    if url:
        _LOGGER.debug('Execute: Container.Update(%s)', url)
        xbmc.executebuiltin('Container.Update({url})'.format(url=url))
    else:
        # URL is a mandatory argument for Container.Update, use Container.Refresh instead
        container_refresh()


def end_of_directory():
    """Close a virtual directory, required to avoid a waiting Kodi"""
    from resources.lib.addon import routing
    xbmcplugin.endOfDirectory(handle=routing.handle, succeeded=False, updateListing=False, cacheToDisc=False)


def jsonrpc(*args, **kwargs):
    """Perform JSONRPC calls"""
    from json import dumps, loads

    # We do not accept both args and kwargs
    if args and kwargs:
        _LOGGER.error('Wrong use of jsonrpc()')
        return None

    # Process a list of actions
    if args:
        for (idx, cmd) in enumerate(args):
            if cmd.get('id') is None:
                cmd.update(id=idx)
            if cmd.get('jsonrpc') is None:
                cmd.update(jsonrpc='2.0')
        return loads(xbmc.executeJSONRPC(dumps(args)))

    # Process a single action
    if kwargs.get('id') is None:
        kwargs.update(id=0)
    if kwargs.get('jsonrpc') is None:
        kwargs.update(jsonrpc='2.0')
    return loads(xbmc.executeJSONRPC(dumps(kwargs)))


def listdir(path):
    """Return all files in a directory (using xbmcvfs)"""
    from xbmcvfs import listdir as vfslistdir
    return vfslistdir(path)


def delete(path):
    """Remove a file (using xbmcvfs)"""
    from xbmcvfs import delete as vfsdelete
    return vfsdelete(path)
