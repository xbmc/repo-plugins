"""
    tknorris shared module

    Copyright (C) 2016 tknorris
    Copyright (C) 2016-2018 Twitch-on-Kodi

    Modified by Twitch-on-Kodi/plugin.video.twitch Dec. 12, 2016

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from xbmc import PLAYLIST_VIDEO, PLAYLIST_MUSIC  # NOQA

import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs

import sys
import os
import re
import json
import time
from urllib.parse import urlencode
from urllib.parse import parse_qs

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

try:
    addon = xbmcaddon.Addon()
except RuntimeError:
    addon = xbmcaddon.Addon('plugin.video.twitch')  # RunScript

get_setting = addon.getSetting
show_settings = addon.openSettings
execute_builtin = xbmc.executebuiltin
get_info_label = xbmc.getInfoLabel
sleep = xbmc.sleep
__log = xbmc.log

Addon = xbmcaddon.Addon
Dialog = xbmcgui.Dialog
PlayList = xbmc.PlayList
Player = xbmc.Player
Window = xbmcgui.Window


def decode_utf8(string):
    try:
        return string.decode('utf-8')
    except AttributeError:
        return string


def is_unicode(string):
    return False


def execute_jsonrpc(command):
    if not isinstance(command, str):
        command = json.dumps(command)
    response = xbmc.executeJSONRPC(command)
    return json.loads(response)


def get_path():
    return decode_utf8(addon.getAddonInfo('path'))


def get_profile():
    return decode_utf8(addon.getAddonInfo('profile'))


def translate_path(path):
    return decode_utf8(xbmc.translatePath(path))


def set_setting(id, value):
    if not isinstance(value, str): value = str(value)
    addon.setSetting(id, value)


def accumulate_setting(setting, addend=1):
    cur_value = get_setting(setting)
    cur_value = int(cur_value) if cur_value else 0
    set_setting(setting, cur_value + addend)


def get_version():
    return addon.getAddonInfo('version')


def get_id():
    return addon.getAddonInfo('id')


def get_name():
    return addon.getAddonInfo('name')


def get_description():
    return decode_utf8(addon.getAddonInfo('description'))


def has_addon(addon_id):
    return xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id) == 1


def addon_enabled(addon_id):
    rpc_request = {"jsonrpc": "2.0",
                   "method": "Addons.GetAddonDetails",
                   "id": 1,
                   "params": {"addonid": "%s" % addon_id,
                              "properties": ["enabled"]}
                   }
    response = execute_jsonrpc(rpc_request)
    try:
        return response['result']['addon']['enabled'] is True
    except KeyError:
        message = response['error']['message']
        code = response['error']['code']
        error = 'Requested |%s| received error |%s| and code: |%s|' % (rpc_request, message, code)
        xbmc.log(error, xbmc.LOGDEBUG)
        return None


def set_addon_enabled(addon_id, enabled=True):
    rpc_request = {"jsonrpc": "2.0",
                   "method": "Addons.SetAddonEnabled",
                   "id": 1,
                   "params": {"addonid": "%s" % addon_id,
                              "enabled": enabled}
                   }
    response = execute_jsonrpc(rpc_request)
    try:
        return response['result'] == 'OK'
    except KeyError:
        message = response['error']['message']
        code = response['error']['code']
        error = 'Requested |%s| received error |%s| and code: |%s|' % (rpc_request, message, code)
        xbmc.log(error, xbmc.LOGDEBUG)
        return False


def get_icon():
    return translate_path('special://home/addons/{0!s}/resources/media/icon.png'.format(get_id()))


def get_thumb(filename):
    return translate_path('special://home/addons/{0!s}/resources/media/thumbnails/{1!s}'.format(get_id(), filename))


def get_fanart():
    return translate_path('special://home/addons/{0!s}/resources/media/fanart.jpg'.format(get_id()))


def get_kodi_version():
    class MetaClass(type):
        def __str__(self):
            return '|%s| |%s| -> |%s|%s|%s|%s|%s|' % (self.application, self.version, self.major, self.minor, self.tag, self.tag_version, self.revision)

    class KodiVersion(object):
        __metaclass__ = MetaClass
        _json_query = execute_jsonrpc({"jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["name"]}, "id": 1})
        application = 'Unknown'
        if ('result' in _json_query) and ('name' in _json_query['result']):
            application = decode_utf8(_json_query['result']['name'])
        version = decode_utf8(xbmc.getInfoLabel('System.BuildVersion'))
        match = re.search('([0-9]+)\.([0-9]+)', version)
        if match: major, minor = match.groups()
        match = re.search('-([a-zA-Z]+)([0-9]*)', version)
        if match: tag, tag_version = match.groups()
        match = re.search('\w+:(\w+-\w+)', version)
        if match: revision = match.group(1)

        try:
            major = int(major)
        except:
            major = 0
        try:
            minor = int(minor)
        except:
            minor = 0
        try:
            revision = decode_utf8(revision)
        except:
            revision = u''
        try:
            tag = decode_utf8(tag)
        except:
            tag = u''
        try:
            tag_version = int(tag_version)
        except:
            tag_version = 0

    return KodiVersion


def get_plugin_url(queries):
    try:
        query = urlencode(queries)
    except UnicodeEncodeError:
        for k in queries:
            if is_unicode(queries[k]):
                queries[k] = queries[k].encode('utf-8')
        query = urlencode(queries)

    return sys.argv[0] + '?' + query


def end_of_directory(cache_to_disc=False, succeeded=True):
    xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=succeeded, cacheToDisc=cache_to_disc)


def set_resolved_url(listitem, succeeded=True):
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), succeeded=succeeded, listitem=listitem)


def set_content(content):
    xbmcplugin.setContent(int(sys.argv[1]), content)


def create_item(item_dict, add=True):
    path = item_dict.get('path', '')
    path = path if isinstance(path, str) else get_plugin_url(path)
    list_item = ListItem(label=item_dict.get('label', ''), label2=item_dict.get('label2', ''), path=path)
    thumbfile = item_dict.get('thumbfile', None)

    icon = get_icon()
    thumb = get_thumb(thumbfile) if thumbfile else icon
    fanart = get_fanart()
    art = item_dict.get('art', {'icon': icon, 'thumb': thumb, 'fanart': fanart})
    if not art.get('icon', None):
        art['icon'] = icon
    if not art.get('thumb', None):
        art['thumb'] = icon
    if not art.get('fanart', None):
        art['fanart'] = fanart
    list_item.setArt(art)

    content_type = item_dict.get('content_type', 'video')
    info = item_dict.get('info', {'title': list_item.getLabel(), 'plot': get_description()})
    list_item.setInfo(content_type, infoLabels=info)

    context_menu = item_dict.get('context_menu', [])
    list_item.addContextMenuItems(context_menu, replaceItems=item_dict.get('replace_menu', False))
    if add:
        add_item(item_dict, list_item)
    else:
        return list_item


def add_item(item_dict, list_item):
    path = item_dict.get('path', None)
    if not path: return

    is_playable = item_dict.get('is_playable', False)
    is_folder = item_dict.get('is_folder', not is_playable)

    list_item.setProperty('isPlayable', str(is_playable).lower())

    url = path if isinstance(path, str) else get_plugin_url(path)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isFolder=is_folder, totalItems=item_dict.get('total_items', 0))


def parse_query(query):
    q = {'mode': 'main'}
    if query.startswith('?'): query = query[1:]
    queries = parse_qs(query)
    for key in queries:
        if len(queries[key]) == 1:
            q[key] = queries[key][0]
        else:
            q[key] = queries[key]
    return q


def notify(header=None, msg='', duration=2000, sound=None, icon_path=None):
    if header is None: header = get_name()
    if sound is None: sound = get_setting('mute_notifications') == 'false'
    if icon_path is None: icon_path = get_icon()
    try:
        xbmcgui.Dialog().notification(header, msg, icon_path, duration, sound)
    except:
        builtin = "Notification(%s,%s, %s, %s)" % (header, msg, duration, icon_path)
        xbmc.executebuiltin(builtin)


def close_all():
    xbmc.executebuiltin('Dialog.Close(all)')


def get_current_window_dialog_id():
    return xbmcgui.getCurrentWindowDialogId()


def get_current_view():
    skinPath = translate_path('special://skin/')
    xml = os.path.join(skinPath, 'addon.xml')
    f = xbmcvfs.File(xml)
    read = f.read()
    f.close()
    try:
        src = re.search('defaultresolution="([^"]+)', read, re.DOTALL).group(1)
    except:
        src = re.search('<res.+?folder="([^"]+)', read, re.DOTALL).group(1)
    src = os.path.join(skinPath, src, 'MyVideoNav.xml')
    f = xbmcvfs.File(src)
    read = f.read()
    f.close()
    match = re.search('<views>([^<]+)', read, re.DOTALL)
    if match:
        views = match.group(1)
        for view in views.split(','):
            if xbmc.getInfoLabel('Control.GetLabel(%s)' % view): return view


def set_view(content, set_view=False, set_sort=False):
    # set content type so library shows more views and info
    if content:
        set_content(content)

    if set_view:
        view = get_setting('%s_view' % content)
        if view and view != '0':
            __log('Setting View to %s (%s)' % (view, content), xbmc.LOGDEBUG)
            xbmc.executebuiltin('Container.SetViewMode(%s)' % view)

    # set sort methods - probably we don't need all of them
    if set_sort:
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)


def refresh_container():
    xbmc.executebuiltin('Container.Refresh')


def update_container(url):
    xbmc.executebuiltin('Container.Update(%s)' % url)


def delete_file(filename):
    return xbmcvfs.delete(filename)


def get_keyboard(heading, default=''):
    keyboard = xbmc.Keyboard()
    keyboard.setHeading(heading)
    if default: keyboard.setDefault(default)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText().strip()
    else:
        return None


class Translations(object):
    def __init__(self, strings):
        self.strings = strings

    def i18n(self, string_id):
        try:
            return addon.getLocalizedString(self.strings[string_id])
        except Exception as e:
            xbmc.log('%s: Failed String Lookup: %s (%s)' % (get_name(), string_id, e), xbmc.LOGWARNING)
            return string_id


class WorkingDialog(object):
    wd = None

    def __init__(self):
        try:
            self.wd = xbmcgui.DialogBusy()
            self.wd.create()
            self.update(0)
        except:
            xbmc.executebuiltin('ActivateWindow(busydialog)')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.wd is not None:
            self.wd.close()
        else:
            xbmc.executebuiltin('Dialog.Close(busydialog)')

    def is_canceled(self):
        if self.wd is not None:
            return self.wd.iscanceled()
        else:
            return False

    def update(self, percent):
        if self.wd is not None:
            self.wd.update(percent)


class ProgressDialog(object):
    pd = None

    def __init__(self, heading, line1=None, line2=None, line3=None, background=False, active=True, timer=0):
        self.begin = time.time()
        self.timer = timer
        self.background = background
        self.heading = heading
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3

        if active and not timer:
            self.pd = self.__create_dialog(line1, line2, line3)
            self.pd.update(0)

    def __create_dialog(self, line1, line2, line3):
        if self.background:
            pd = xbmcgui.DialogProgressBG()
            msg = self.__formatted_message(line1, line2, line3, bg=True)
            pd.create(self.heading, msg)
        else:
            pd = xbmcgui.DialogProgress()
            pd.create(self.heading, self.__formatted_message(line1, line2, line3, bg=False))
        return pd

    def __formatted_message(self, line1, line2, line3, bg=True):
        lines = ['', '', '']

        whitespace = '' if bg else '[CR]'

        if line1 is None:
            lines[0] = whitespace if self.line1 is None else self.line1
        else:
            lines[0] = line1

        if line2 is None:
            lines[1] = whitespace if self.line2 is None else self.line2
        else:
            lines[1] = line2

        if line3 is None:
            lines[2] = '' if self.line3 is None else self.line3
        else:
            lines[2] = line3

        whitespace = ' ' if bg else '[CR]'

        return whitespace.join(lines)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.pd is not None:
            self.pd.close()

    def is_canceled(self):
        if self.pd is not None and not self.background:
            return self.pd.iscanceled()
        else:
            return False

    def update(self, percent, line1=None, line2=None, line3=None):
        if self.pd is None and self.timer and (time.time() - self.begin) >= self.timer:
            self.pd = self.__create_dialog(line1, line2, line3)

        if line1 is not None:
            self.line1 = line1
        if line2 is not None:
            self.line2 = line2
        if line2 is not None:
            self.line2 = line2

        if self.pd is not None:
            if self.background:
                msg = self.__formatted_message(line1, line2, line3, bg=True)
                self.pd.update(percent, self.heading, msg)
            else:
                self.pd.update(percent, self.__formatted_message(line1, line2, line3, bg=False))


class CountdownDialog(object):
    __INTERVALS = 5
    pd = None

    def __init__(self, heading, line1=None, line2=None, line3=None, active=True, countdown=60, interval=5):
        self.heading = heading
        self.countdown = countdown
        self.interval = interval
        self.line1 = line1
        self.line2 = line2
        self.line3 = line3
        if active:
            pd = xbmcgui.DialogProgress()
            if not self.line3: line3 = 'Expires in: %s seconds' % countdown
            pd.create(self.heading, self.__formatted_message(line1, line2, line3))
            pd.update(100)
            self.pd = pd

    def __formatted_message(self, line1, line2, line3):
        lines = []

        if line1 is None:
            lines[0] = '[CR]' if self.line1 is None else self.line1
        else:
            lines[0] = line1

        if line2 is None:
            lines[1] = '[CR]' if self.line2 is None else self.line2
        else:
            lines[1] = line2

        if line3 is None:
            lines[2] = '' if self.line3 is None else self.line3
        else:
            lines[2] = line3

        return '[CR]'.join(lines)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.pd is not None:
            self.pd.close()

    def start(self, func, args=None, kwargs=None):
        if args is None: args = []
        if kwargs is None: kwargs = {}
        result = func(*args, **kwargs)
        if result:
            return result

        start = time.time()
        expires = time_left = int(self.countdown)
        interval = self.interval
        while time_left > 0:
            for _ in range(CountdownDialog.__INTERVALS):
                sleep(interval * 1000 / CountdownDialog.__INTERVALS)
                if self.is_canceled(): return
                time_left = expires - int(time.time() - start)
                if time_left < 0: time_left = 0
                progress = time_left * 100 / expires
                line3 = 'Expires in: %s seconds' % time_left if not self.line3 else ''
                self.update(progress, line3=line3)

            result = func(*args, **kwargs)
            if result:
                return result

    def is_canceled(self):
        if self.pd is None:
            return False
        else:
            return self.pd.iscanceled()

    def update(self, percent, line1=None, line2=None, line3=None):
        if line1 is not None:
            self.line1 = line1
        if line2 is not None:
            self.line2 = line2
        if line2 is not None:
            self.line2 = line2

        if self.pd is not None:
            self.pd.update(percent, self.__formatted_message(line1, line2, line3))


class ListItem(xbmcgui.ListItem):
    def setArt(self, dictionary):
        if get_kodi_version().major < 16 and 'icon' in dictionary:
            self.setIconImage(dictionary['icon'])
            del dictionary['icon']
        super(ListItem, self).setArt(dictionary)
