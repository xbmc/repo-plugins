# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""All functionality that requires Kodi imports"""

from __future__ import absolute_import, division, unicode_literals
from contextlib import contextmanager
from sys import version_info
from socket import timeout
from ssl import SSLError

import xbmc
import xbmcplugin

try:  # Kodi 19 alpha 2 and higher
    from xbmcvfs import translatePath
except ImportError:  # Kodi 19 alpha 1 and lower
    from xbmc import translatePath  # pylint: disable=ungrouped-imports

from xbmcaddon import Addon
from utils import from_unicode, to_unicode

try:  # Python 3
    from urllib.request import HTTPErrorProcessor
except ImportError:  # Python 2
    from urllib2 import HTTPErrorProcessor

ADDON = Addon()
DEFAULT_CACHE_DIR = 'cache'

SORT_METHODS = dict(
    # date=xbmcplugin.SORT_METHOD_DATE,
    dateadded=xbmcplugin.SORT_METHOD_DATEADDED,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    # genre=xbmcplugin.SORT_METHOD_GENRE,
    # label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    label=xbmcplugin.SORT_METHOD_LABEL,
    title=xbmcplugin.SORT_METHOD_TITLE,
    # none=xbmcplugin.SORT_METHOD_UNSORTED,
    # FIXME: We would like to be able to sort by unprefixed title (ignore date/episode prefix)
    # title=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
)

WEEKDAY_LONG = {
    '0': xbmc.getLocalizedString(17),
    '1': xbmc.getLocalizedString(11),
    '2': xbmc.getLocalizedString(12),
    '3': xbmc.getLocalizedString(13),
    '4': xbmc.getLocalizedString(14),
    '5': xbmc.getLocalizedString(15),
    '6': xbmc.getLocalizedString(16),
}

MONTH_LONG = {
    '01': xbmc.getLocalizedString(21),
    '02': xbmc.getLocalizedString(22),
    '03': xbmc.getLocalizedString(23),
    '04': xbmc.getLocalizedString(24),
    '05': xbmc.getLocalizedString(25),
    '06': xbmc.getLocalizedString(26),
    '07': xbmc.getLocalizedString(27),
    '08': xbmc.getLocalizedString(28),
    '09': xbmc.getLocalizedString(29),
    '10': xbmc.getLocalizedString(30),
    '11': xbmc.getLocalizedString(31),
    '12': xbmc.getLocalizedString(32),
}

WEEKDAY_SHORT = {
    '0': xbmc.getLocalizedString(47),
    '1': xbmc.getLocalizedString(41),
    '2': xbmc.getLocalizedString(42),
    '3': xbmc.getLocalizedString(43),
    '4': xbmc.getLocalizedString(44),
    '5': xbmc.getLocalizedString(45),
    '6': xbmc.getLocalizedString(46),
}

MONTH_SHORT = {
    '01': xbmc.getLocalizedString(51),
    '02': xbmc.getLocalizedString(52),
    '03': xbmc.getLocalizedString(53),
    '04': xbmc.getLocalizedString(54),
    '05': xbmc.getLocalizedString(55),
    '06': xbmc.getLocalizedString(56),
    '07': xbmc.getLocalizedString(57),
    '08': xbmc.getLocalizedString(58),
    '09': xbmc.getLocalizedString(59),
    '10': xbmc.getLocalizedString(60),
    '11': xbmc.getLocalizedString(61),
    '12': xbmc.getLocalizedString(62),
}


class NoRedirection(HTTPErrorProcessor):
    """Prevent urllib from following http redirects"""

    def http_response(self, request, response):
        return response

    https_response = http_response


class SafeDict(dict):
    """A safe dictionary implementation that does not break down on missing keys"""
    def __missing__(self, key):
        """Replace missing keys with the original placeholder"""
        return '{' + key + '}'


def addon_icon():
    """Return add-on icon"""
    return get_addon_info('icon')


def addon_id():
    """Return add-on ID"""
    return get_addon_info('id')


def addon_fanart():
    """Return add-on fanart"""
    return get_addon_info('fanart')


def addon_name():
    """Return add-on name"""
    return get_addon_info('name')


def addon_path():
    """Return add-on path"""
    return get_addon_info('path')


def translate_path(path):
    """Converts a Kodi special:// path to the corresponding OS-specific path"""
    return to_unicode(translatePath(from_unicode(path)))


def addon_profile():
    """Return add-on profile"""
    return translate_path(ADDON.getAddonInfo('profile'))


def url_for(name, *args, **kwargs):
    """Wrapper for routing.url_for() to lookup by name"""
    import addon
    return addon.plugin.url_for(getattr(addon, name), *args, **kwargs)


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
            category_label = 'VRT NU / '
        if plugin.path.startswith(('/favorites/', '/resumepoints/')):
            category_label += localize(30428) + ' / '  # My
        if isinstance(category, int):
            category_label += localize(category)
        else:
            category_label += category
    elif not content:
        category_label = 'VRT NU'
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

        prop_dict = dict(
            IsInternetStream='true' if is_playable else 'false',
            IsPlayable='true' if is_playable else 'false',
            IsFolder='false' if is_folder else 'true',
        )
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
                title_item.art_dict = dict(fanart=addon_fanart())
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


def play(stream, video=None):
    """Create a virtual directory listing to play its only item"""
    try:  # Python 3
        from urllib.parse import unquote
    except ImportError:  # Python 2
        from urllib2 import unquote

    from xbmcgui import ListItem
    from addon import plugin

    play_item = ListItem(path=stream.stream_url)
    if video and hasattr(video, 'info_dict'):
        play_item.setProperty('subtitle', video.label)
        play_item.setArt(video.art_dict)
        play_item.setInfo(
            type='video',
            infoLabels=video.info_dict
        )
    play_item.setProperty('inputstream.adaptive.max_bandwidth', str(get_max_bandwidth() * 1000))
    play_item.setProperty('network.bandwidth', str(get_max_bandwidth() * 1000))

    if stream.stream_url is not None and stream.use_inputstream_adaptive:
        if kodi_version_major() < 19:
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
        else:
            play_item.setProperty('inputstream', 'inputstream.adaptive')

        play_item.setContentLookup(False)

        if '.mpd' in stream.stream_url:
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            play_item.setMimeType('application/dash+xml')

        if '.m3u8' in stream.stream_url:
            play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            play_item.setMimeType('application/vnd.apple.mpegurl')

        if stream.license_key is not None:
            import inputstreamhelper
            is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
            if is_helper.check_inputstream():
                play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                play_item.setProperty('inputstream.adaptive.license_key', stream.license_key)

    subtitles_visible = get_setting_bool('showsubtitles', default=True)
    # Separate subtitle url for hls-streams
    if subtitles_visible and stream.subtitle_url is not None:
        log(2, 'Subtitle URL: {url}', url=unquote(stream.subtitle_url))
        play_item.setSubtitles([stream.subtitle_url])

    log(1, 'Play: {url}', url=unquote(stream.stream_url))
    xbmcplugin.setResolvedUrl(plugin.handle, bool(stream.stream_url), listitem=play_item)

    while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
        xbmc.sleep(100)
    xbmc.Player().showSubtitles(subtitles_visible)


def get_search_string(search_string=None):
    """Ask the user for a search string"""
    keyboard = xbmc.Keyboard(search_string, localize(30134))
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
        return Dialog().ok(heading=heading, line1=message)
    return Dialog().ok(heading=heading, message=message)


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
    return Dialog().multiselect(heading=heading, options=options, autoclose=autoclose, preselect=preselect, useDetails=use_details)


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
            log(3, "Your system does not support locale '{locale}': {error}", locale=locale_lang, error=exc)
            set_locale.cached = False
            return False
    set_locale.cached = True
    return True


def localize(string_id, **kwargs):
    """Return the translated string from the .po language files, optionally translating variables"""
    if not isinstance(string_id, int) and not string_id.isdecimal():
        return string_id
    if kwargs:
        from string import Formatter
        return Formatter().vformat(ADDON.getLocalizedString(string_id), (), SafeDict(**kwargs))
    return ADDON.getLocalizedString(string_id)


def localize_time(time):
    """Localize time format"""
    time_format = xbmc.getRegion('time')

    # Fix a bug in Kodi v18.5 and older causing double hours
    # https://github.com/xbmc/xbmc/pull/17380
    time_format = time_format.replace('%H%H:', '%H:')

    # Strip off seconds
    time_format = time_format.replace(':%S', '')

    return time.strftime(time_format)


def localize_date(date, strftime):
    """Return a localized date, even if the system does not support your locale"""
    has_locale = set_locale()
    # When locale is supported, return original format
    if has_locale:
        return date.strftime(strftime)
    # When locale is unsupported, translate weekday and month
    if '%A' in strftime:
        strftime = strftime.replace('%A', WEEKDAY_LONG[date.strftime('%w')])
    elif '%a' in strftime:
        strftime = strftime.replace('%a', WEEKDAY_SHORT[date.strftime('%w')])
    if '%B' in strftime:
        strftime = strftime.replace('%B', MONTH_LONG[date.strftime('%m')])
    elif '%b' in strftime:
        strftime = strftime.replace('%b', MONTH_SHORT[date.strftime('%m')])

    # %e isn't supported on Python 2.7 on Windows
    if '%e' in strftime:
        strftime = strftime.replace('%e', str(int(date.strftime('%d'))))

    return date.strftime(strftime)


def localize_datelong(date):
    """Return a localized long date string"""
    return localize_date(date, xbmc.getRegion('datelong'))


def localize_from_data(name, data):
    """Return a localized name string from a Dutch data object"""
    # Return if Kodi language is Dutch
    if get_global_setting('locale.language') == 'resource.language.nl_nl':
        return name
    return next((localize(item.get('msgctxt')) for item in data if item.get('name') == name), name)


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
    """Get an add-on setting as float"""
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


def get_advanced_setting(key, default=None):
    """Get a setting from advancedsettings.xml"""
    as_path = translate_path('special://masterprofile/advancedsettings.xml')
    if not exists(as_path):
        return default
    from xml.etree.ElementTree import parse, ParseError
    try:
        as_root = parse(as_path).getroot()
    except ParseError:
        return default
    value = as_root.find(key)
    if value is not None:
        if value.text is None:
            return default
        return value.text
    return default


def get_advanced_setting_int(key, default=0):
    """Get a setting from advancedsettings.xml as an integer"""
    if not isinstance(default, int):
        default = 0
    setting = get_advanced_setting(key, default)
    if not isinstance(setting, int):
        setting = int(setting.strip()) if setting.strip().isdigit() else default
    return setting


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


def notify(sender, message, data):
    """Send a notification to Kodi using JSON RPC"""
    result = jsonrpc(method='JSONRPC.NotifyAll', params=dict(
        sender=sender,
        message=message,
        data=data,
    ))
    if result.get('result') != 'OK':
        log_error('Failed to send notification: {error}', error=result.get('error').get('message'))
        return False
    log(2, 'Succesfully sent notification')
    return True


def get_playerid():
    """Get current playerid"""
    result = {}
    while not result.get('result'):
        result = jsonrpc(method='Player.GetActivePlayers')
    return result.get('result', [{}])[0].get('playerid')


def get_max_bandwidth():
    """Get the max bandwidth based on Kodi and add-on settings"""
    vrtnu_max_bandwidth = int(get_setting('max_bandwidth', default='0'))
    global_max_bandwidth = int(get_global_setting('network.bandwidth'))
    if vrtnu_max_bandwidth != 0 and global_max_bandwidth != 0:
        return min(vrtnu_max_bandwidth, global_max_bandwidth)
    if vrtnu_max_bandwidth != 0:
        return vrtnu_max_bandwidth
    if global_max_bandwidth != 0:
        return global_max_bandwidth
    return 0


def has_socks():
    """Test if socks is installed, and use a static variable to remember"""
    if hasattr(has_socks, 'cached'):
        return getattr(has_socks, 'cached')
    try:
        import socks  # noqa: F401; pylint: disable=unused-variable,unused-import
    except ImportError:
        has_socks.cached = False
        return None  # Detect if this is the first run
    has_socks.cached = True
    return True


def get_proxies():
    """Return a usable proxies dictionary from Kodi proxy settings"""
    usehttpproxy = get_global_setting('network.usehttpproxy')
    if usehttpproxy is not True:
        return None

    try:
        httpproxytype = int(get_global_setting('network.httpproxytype'))
    except ValueError:
        httpproxytype = 0

    socks_supported = has_socks()
    if httpproxytype != 0 and not socks_supported:
        # Only open the dialog the first time (to avoid multiple popups)
        if socks_supported is None:
            ok_dialog('', localize(30966))  # Requires PySocks
        return None

    proxy_types = ['http', 'socks4', 'socks4a', 'socks5', 'socks5h']

    proxy = dict(
        scheme=proxy_types[httpproxytype] if 0 <= httpproxytype < 5 else 'http',
        server=get_global_setting('network.httpproxyserver'),
        port=get_global_setting('network.httpproxyport'),
        username=get_global_setting('network.httpproxyusername'),
        password=get_global_setting('network.httpproxypassword'),
    )

    if proxy.get('username') and proxy.get('password') and proxy.get('server') and proxy.get('port'):
        proxy_address = '{scheme}://{username}:{password}@{server}:{port}'.format(**proxy)
    elif proxy.get('username') and proxy.get('server') and proxy.get('port'):
        proxy_address = '{scheme}://{username}@{server}:{port}'.format(**proxy)
    elif proxy.get('server') and proxy.get('port'):
        proxy_address = '{scheme}://{server}:{port}'.format(**proxy)
    elif proxy.get('server'):
        proxy_address = '{scheme}://{server}'.format(**proxy)
    else:
        return None

    return dict(http=proxy_address, https=proxy_address)


def get_cond_visibility(condition):
    """Test a condition in XBMC"""
    return xbmc.getCondVisibility(condition)


def has_inputstream_adaptive():
    """Whether InputStream Adaptive is installed and enabled in add-on settings"""
    return get_setting_bool('useinputstreamadaptive', default=True) and has_addon('inputstream.adaptive')


def has_addon(name):
    """Checks if add-on is installed and enabled"""
    if kodi_version_major() < 19:
        return xbmc.getCondVisibility('System.HasAddon(%s)' % name) == 1
    return xbmc.getCondVisibility('System.AddonIsEnabled(%s)' % name) == 1


def has_credentials():
    """Whether the add-on has credentials filled in"""
    return bool(get_setting('username') and get_setting('password'))


def kodi_version():
    """Returns full Kodi version as string"""
    return xbmc.getInfoLabel('System.BuildVersion').split(' ')[0]


def kodi_version_major():
    """Returns major Kodi version as integer"""
    return int(kodi_version().split('.')[0])


def can_play_drm():
    """Whether this Kodi can do DRM using InputStream Adaptive"""
    return get_setting_bool('usedrm', default=True) and get_setting_bool('useinputstreamadaptive', default=True) and supports_drm()


def supports_drm():
    """Whether this Kodi version supports DRM decryption using InputStream Adaptive"""
    return kodi_version_major() > 17


COLOUR_THEMES = dict(
    dark=dict(highlighted='yellow', availability='blue', geoblocked='red', greyedout='gray'),
    light=dict(highlighted='brown', availability='darkblue', geoblocked='darkred', greyedout='darkgray'),
    custom=dict(
        highlighted=get_setting('colour_highlighted'),
        availability=get_setting('colour_availability'),
        geoblocked=get_setting('colour_geoblocked'),
        greyedout=get_setting('colour_greyedout')
    )
)


def themecolour(kind):
    """Get current theme color by kind (highlighted, availability, geoblocked, greyedout)"""
    theme = get_setting('colour_theme', 'dark')
    color = COLOUR_THEMES.get(theme).get(kind, COLOUR_THEMES.get('dark').get(kind))
    return color


def colour(text):
    """Convert stub color bbcode into colors from the settings"""
    theme = get_setting('colour_theme', 'dark')
    try:
        text = text.format(**COLOUR_THEMES.get(theme))
    except KeyError:
        log_error('BBCode colouring failed.')
    return text


def get_cache_path(cache_file, cache_dir=DEFAULT_CACHE_DIR):
    """Return a specified cache path"""
    import os
    cache_dir = get_cache_dir(cache_dir)
    return os.path.join(cache_dir, cache_file)


def get_cache_dir(cache_dir=DEFAULT_CACHE_DIR):
    """Create and return a specified cache directory"""
    import os
    cache_dir = os.path.join(addon_profile(), cache_dir, '')
    return cache_dir


def get_addon_info(key):
    """Return addon information"""
    return to_unicode(ADDON.getAddonInfo(key))


def listdir(path):
    """Return all files in a directory (using xbmcvfs)"""
    from xbmcvfs import listdir as vfslistdir
    return vfslistdir(path)


def mkdir(path):
    """Create a directory (using xbmcvfs)"""
    from xbmcvfs import mkdir as vfsmkdir
    log(3, "Create directory '{path}'.", path=path)
    return vfsmkdir(path)


def mkdirs(path):
    """Create directory including parents (using xbmcvfs)"""
    from xbmcvfs import mkdirs as vfsmkdirs
    log(3, "Recursively create directory '{path}'.", path=path)
    return vfsmkdirs(path)


def exists(path):
    """Whether the path exists (using xbmcvfs)"""
    from xbmcvfs import exists as vfsexists
    return vfsexists(path)


@contextmanager
def open_file(path, flags='r'):
    """Open a file (using xbmcvfs)"""
    from xbmcvfs import File
    fdesc = File(path, flags)
    yield fdesc
    fdesc.close()


def stat_file(path):
    """Return information about a file (using xbmcvfs)"""
    from xbmcvfs import Stat
    return Stat(path)


def delete(path):
    """Remove a file (using xbmcvfs)"""
    from xbmcvfs import delete as vfsdelete
    log(3, "Delete file '{path}'.", path=path)
    return vfsdelete(path)


def delete_cached_thumbnail(url):
    """Remove a cached thumbnail from Kodi in an attempt to get a realtime live screenshot"""
    # Get texture
    result = jsonrpc(method='Textures.GetTextures', params=dict(
        filter=dict(
            field='url',
            operator='is',
            value=url,
        ),
    ))
    if result.get('result', {}).get('textures') is None:
        log_error('URL {url} not found in texture cache', url=url)
        return False

    texture_id = next((texture.get('textureid') for texture in result.get('result').get('textures')), None)
    if not texture_id:
        log_error('URL {url} not found in texture cache', url=url)
        return False
    log(2, 'found texture_id {id} for url {url} in texture cache', id=texture_id, url=url)

    # Remove texture
    result = jsonrpc(method='Textures.RemoveTexture', params=dict(textureid=texture_id))
    if result.get('result') != 'OK':
        log_error('failed to remove {url} from texture cache: {error}', url=url, error=result.get('error', {}).get('message'))
        return False

    log(2, 'succesfully removed {url} from texture cache', url=url)
    return True


def input_down():
    """Move the cursor down"""
    jsonrpc(method='Input.Down')


def current_container_url():
    """Get current container plugin:// url"""
    url = xbmc.getInfoLabel('Container.FolderPath')
    if url == '':
        return None
    return url


def container_refresh(url=None):
    """Refresh the current container or (re)load a container by URL"""
    if url:
        log(3, 'Execute: Container.Refresh({url})', url=url)
        xbmc.executebuiltin('Container.Refresh({url})'.format(url=url))
    else:
        log(3, 'Execute: Container.Refresh')
        xbmc.executebuiltin('Container.Refresh')


def container_update(url):
    """Update the current container while respecting the path history."""
    if url:
        log(3, 'Execute: Container.Update({url})', url=url)
        xbmc.executebuiltin('Container.Update({url})'.format(url=url))
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


def execute_builtin(builtin):
    """Run an internal Kodi builtin"""
    xbmc.executebuiltin(builtin)


def end_of_directory():
    """Close a virtual directory, required to avoid a waiting Kodi"""
    from addon import plugin
    xbmcplugin.endOfDirectory(handle=plugin.handle, succeeded=False, updateListing=False, cacheToDisc=False)


def wait_for_resumepoints():
    """Wait for resumepoints to be updated"""
    update = get_property('vrtnu_resumepoints')
    if update == 'busy':
        import time
        time_out = time.time() + 5  # 5 seconds timeout
        log(3, 'Resumepoint update is busy, wait')
        while update != 'ready':
            if time.time() > time_out:  # Exit loop in case something goes wrong
                break
            xbmc.sleep(50)
            update = get_property('vrtnu_resumepoints')
        set_property('vrtnu_resumepoints', None)
        log(3, 'Resumepoint update is ready, continue')
        return True
    return False


def log(level=1, message='', **kwargs):
    """Log info messages to Kodi"""
    debug_logging = get_global_setting('debug.showloginfo')  # Returns a boolean
    max_log_level = get_setting_int('max_log_level', default=0)
    if not debug_logging and not (level <= max_log_level and max_log_level != 0):
        return
    if kwargs:
        from string import Formatter
        message = Formatter().vformat(message, (), SafeDict(**kwargs))
    message = '[{addon}] {message}'.format(addon=addon_id(), message=message)
    xbmc.log(from_unicode(message), level % 3 if debug_logging else 2)


def log_access(argv):
    """Log addon access"""
    log(1, 'Access: {url}{qs}', url=argv[0], qs=argv[2] if len(argv) > 2 else '')


def log_error(message, **kwargs):
    """Log error messages to Kodi"""
    if kwargs:
        from string import Formatter
        message = Formatter().vformat(message, (), SafeDict(**kwargs))
    message = '[{addon}] {message}'.format(addon=addon_id(), message=message)
    xbmc.log(from_unicode(message), 4)


def jsonrpc(*args, **kwargs):
    """Perform JSONRPC calls"""
    from json import dumps, loads

    # We do not accept both args and kwargs
    if args and kwargs:
        log_error('Wrong use of jsonrpc()')
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


def human_delta(seconds):
    """Return a human-readable representation of the TTL"""
    from math import floor
    days = int(floor(seconds / (24 * 60 * 60)))
    seconds = seconds % (24 * 60 * 60)
    hours = int(floor(seconds / (60 * 60)))
    seconds = seconds % (60 * 60)
    if days:
        return '%d day%s and %d hour%s' % (days, 's' if days != 1 else '', hours, 's' if hours != 1 else '')
    minutes = int(floor(seconds / 60))
    seconds = seconds % 60
    if hours:
        return '%d hour%s and %d minute%s' % (hours, 's' if hours != 1 else '', minutes, 's' if minutes != 1 else '')
    if minutes:
        return '%d minute%s and %d second%s' % (minutes, 's' if minutes != 1 else '', seconds, 's' if seconds != 1 else '')
    return '%d second%s' % (seconds, 's' if seconds != 1 else '')


def get_cache(cache_file, ttl=None, cache_dir=DEFAULT_CACHE_DIR):  # pylint: disable=redefined-outer-name
    """Get the content from cache, if it is still fresh"""
    if not get_setting_bool('usehttpcaching', default=True):
        return None

    fullpath = get_cache_path(cache_file, cache_dir)
    if not exists(fullpath):
        return None

    if ttl is not None:
        from time import localtime, mktime
        mtime = stat_file(fullpath).st_mtime()
        now = mktime(localtime())
        if now >= mtime + ttl:
            return None

#    if ttl is None:
#        log(3, "Cache '{path}' is forced from cache.", path=path)
#    else:
#        log(3, "Cache '{path}' is fresh, expires in {time}.", path=path, time=human_delta(mtime + ttl - now))
    with open_file(fullpath, 'r') as fdesc:
        json = get_json_data(fdesc)

    if json is None:
        return None

    if ttl is None and isinstance(json, dict):
        expiration_date = json.get('expirationDate', None)
        if expiration_date:
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            now = datetime.now(dateutil.tz.tzlocal())
            exp = dateutil.parser.parse(expiration_date)
            if exp <= now:
                log(2, "Cache expired: '{path}'", path=fullpath)
                return None
    log(2, "Got item from cache '{path}'", path=fullpath)
    return json


def update_cache(cache_file, data, cache_dir=DEFAULT_CACHE_DIR):
    """Update the cache, if necessary"""
    if not get_setting_bool('usehttpcaching', default=True):
        return

    fullpath = get_cache_path(cache_file, cache_dir)
    if not exists(fullpath):
        # Create cache directory if missing
        directory = get_cache_dir(cache_dir)
        if not exists(directory):
            mkdirs(directory)
        write_cache(fullpath, data)
        return

    with open_file(fullpath, 'r') as fdesc:
        cache = fdesc.read()

    # Avoid writes if possible (i.e. SD cards)
    if cache == data:
        update_timestamp(fullpath)
        return

    write_cache(fullpath, data)


def write_cache(fullpath, data):
    """Write data to cache"""
    log(3, "Write cache '{path}'.", path=fullpath)
    with open_file(fullpath, 'w') as fdesc:
        fdesc.write(data)


def update_timestamp(fullpath):
    """Update a file's timestamp"""
    from os import utime
    log(3, "Cache '{path}' has not changed, updating mtime only.", path=fullpath)
    utime(fullpath, None)


def ttl(kind='direct'):
    """Return the HTTP cache ttl in seconds based on kind of relation"""
    if kind == 'direct':
        return get_setting_int('httpcachettldirect', default=5) * 60
    if kind == 'indirect':
        return get_setting_int('httpcachettlindirect', default=60) * 60
    return 5 * 60


def open_url(url, data=None, headers=None, method=None, cookiejar=None, follow_redirects=True, raise_errors=None):
    """Return a urllib http response"""
    try:  # Python 3
        from urllib.error import HTTPError, URLError
        from urllib.parse import unquote
        from urllib.request import build_opener, HTTPCookieProcessor, ProxyHandler, Request
    except ImportError:  # Python 2
        from urllib2 import build_opener, HTTPError, HTTPCookieProcessor, ProxyHandler, Request, URLError, unquote

    opener_args = []
    if not follow_redirects:
        opener_args.append(NoRedirection)
    if cookiejar is not None:
        opener_args.append(HTTPCookieProcessor(cookiejar))
    proxies = get_proxies()
    if proxies:
        opener_args.append(ProxyHandler(proxies))
    opener = build_opener(*opener_args)

    if not headers:
        headers = {}
    req = Request(url, headers=headers)
    if data is not None:
        req.data = data
        log(2, 'URL post: {url}', url=unquote(url))
        # Make sure we don't log the password
        debug_data = data
        if 'password' in to_unicode(debug_data):
            debug_data = '**redacted**'
        log(2, 'URL post data: {data}', data=debug_data)
    else:
        log(2, 'URL get: {url}', url=unquote(url))

    if method is not None:
        req.get_method = lambda: method

    if raise_errors is None:
        raise_errors = []
    try:
        return opener.open(req)
    except HTTPError as exc:
        if isinstance(raise_errors, list) and 401 in raise_errors or raise_errors == 'all':
            raise
        if hasattr(req, 'selector'):  # Python 3.4+
            url_length = len(req.selector)
        else:  # Python 2.7
            url_length = len(req.get_selector())
        if exc.code == 400 and 7600 <= url_length <= 8192:
            ok_dialog(heading='HTTP Error 400', message=localize(30967))
            log_error('HTTP Error 400: Probably exceeded maximum url length: '
                      'VRT Search API url has a length of {length} characters.', length=url_length)
            return None
        if exc.code == 413 and url_length > 8192:
            ok_dialog(heading='HTTP Error 413', message=localize(30967))
            log_error('HTTP Error 413: Exceeded maximum url length: '
                      'VRT Search API url has a length of {length} characters.', length=url_length)
            return None
        if exc.code == 431:
            ok_dialog(heading='HTTP Error 431', message=localize(30967))
            log_error('HTTP Error 431: Request header fields too large: '
                      'VRT Search API url has a length of {length} characters.', length=url_length)
            return None
        if exc.code == 401:
            ok_dialog(heading='HTTP Error {code}'.format(code=exc.code), message='{}\n{}'.format(url, exc.reason))
            log_error('HTTP Error {code}: {reason}', code=exc.code, reason=exc.reason)
            return None
        if exc.code in (400, 403) and exc.headers.get('Content-Type') and 'application/json' in exc.headers.get('Content-Type'):
            return exc
        ok_dialog(heading='HTTP Error {code}'.format(code=exc.code), message='{}\n{}'.format(url, exc.reason))
        log_error('HTTP Error {code}: {reason}', code=exc.code, reason=exc.reason)
        return None
    except URLError as exc:
        ok_dialog(heading=localize(30968), message=localize(30969))
        log_error('URLError: {error}\nurl: {url}', error=exc.reason, url=url)
        return None
    except SSLError as exc:
        # TODO: Include the error message in the notification window
        ok_dialog(heading=localize(30968), message=localize(30969))
        if hasattr(exc, 'reason'):  # Python 2.7.9+, but still failed on Python 2.7.16
            log_error('SSLError: {error} ({library})\nurl: {url}', error=exc.reason, library=exc.library, url=url)
        elif isinstance(exc, list):
            log_error('SSLError: {error} ({errno})\nurl: {url}', errno=exc[0], error=exc[1], url=url)
        else:
            log_error('SSLError: {error}\nurl: {url}', error=str(exc), url=url)
        return None
    except timeout as exc:
        ok_dialog(heading=localize(30968), message=localize(30969))
        log_error('Timeout: {error}\nurl: {url}', error=exc, url=url)
        return None


def get_json_data(response, fail=None):
    """Return json object from HTTP response"""
    from json import load, loads
    try:
        if (3, 0, 0) <= version_info < (3, 6, 0):  # the JSON object must be str, not 'bytes'
            return loads(to_unicode(response.read()))
        return load(response)
    except TypeError as exc:  # 'NoneType' object is not callable
        log_error('JSON TypeError: {exc}', exc=exc)
        return fail
    except ValueError as exc:  # No JSON object could be decoded
        log_error('JSON ValueError: {exc}', exc=exc)
        return fail


def get_url_json(url, cache=None, headers=None, data=None, fail=None, raise_errors=None):
    """Return HTTP data"""
    response = open_url(url, headers=headers, data=data, raise_errors=raise_errors)
    if response:
        json_data = get_json_data(response, fail=fail)
        if json_data:
            if cache:
                from json import dumps
                update_cache(cache, dumps(json_data))
            return json_data
    return fail


def generate_expiration_date(hours=2):
    """Return ISO 8601 formatted expirationDate"""
    from datetime import datetime, timedelta
    import dateutil.tz
    return (datetime.now(dateutil.tz.UTC) + timedelta(hours=hours)).isoformat()


def delete_cache(cache_file, cache_dir=DEFAULT_CACHE_DIR):
    """Delete a cached file"""
    path = get_cache_path(cache_file, cache_dir)
    if exists(path):
        delete(path)


def get_cached_url_json(url, cache, headers=None, ttl=None, fail=None):  # pylint: disable=redefined-outer-name
    """Return data from cache, if any, else make an HTTP request"""
    # Get api data from cache if it is fresh
    json_data = get_cache(cache, ttl=ttl)
    if json_data is not None:
        return json_data
    return get_url_json(url, cache=cache, headers=headers, fail=fail)


def refresh_caches(cache_file=None):
    """Invalidate the needed caches and refresh container"""
    files = ['favorites.json', 'oneoff.json', 'resume_points.json', 'watchlater.json']
    if cache_file and cache_file not in files:
        files.append(cache_file)
    invalidate_caches(*files)
    container_refresh()
    notification(message=localize(30981))


def invalidate_caches(*caches):
    """Invalidate multiple cache files"""
    import fnmatch
    _, files = listdir(get_cache_dir())
    # Invalidate caches related to menu list refreshes
    removes = set()
    for expr in caches:
        removes.update(fnmatch.filter(files, expr))
    for filename in removes:
        delete(get_cache_path(filename))
