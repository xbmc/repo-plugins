"""
    tknorris shared module
    Copyright (C) 2016 tknorris

    Modified by Twitch-on-Kodi/plugin.video.twitch Dec. 12, 2016

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from xbmc import PLAYLIST_VIDEO, PLAYLIST_MUSIC
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import xbmcvfs
import urllib
import urlparse
import sys
import os
import re
import json
import time

addon = xbmcaddon.Addon()
get_setting = addon.getSetting
show_settings = addon.openSettings
execute_builtin = xbmc.executebuiltin
get_info_label = xbmc.getInfoLabel
sleep = xbmc.sleep
__log = xbmc.log

Dialog = xbmcgui.Dialog
PlayList = xbmc.PlayList
Player = xbmc.Player
Window = xbmcgui.Window


def execute_jsonrpc(command):
    if not isinstance(command, basestring):
        command = json.dumps(command)
    response = xbmc.executeJSONRPC(command)
    return json.loads(response)


def get_path():
    return addon.getAddonInfo('path').decode('utf-8')


def get_profile():
    return addon.getAddonInfo('profile').decode('utf-8')


def translate_path(path):
    return xbmc.translatePath(path).decode('utf-8')


def set_setting(id, value):
    if not isinstance(value, basestring): value = str(value)
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
    return addon.getAddonInfo('description').decode('utf-8')


def has_addon(addon_id):
    return xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id) == 1


def get_icon():
    return translate_path('special://home/addons/{0!s}/icon.png'.format(get_id()))


def get_fanart():
    return translate_path('special://home/addons/{0!s}/fanart.png'.format(get_id()))


def get_kodi_version():
    class MetaClass(type):
        def __str__(self):
            return '|%s| -> |%s|%s|%s|%s|%s|' % (self.version, self.major, self.minor, self.tag, self.tag_version, self.revision)

    class KodiVersion(object):
        __metaclass__ = MetaClass
        version = xbmc.getInfoLabel('System.BuildVersion').decode('utf-8')
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
            revision = revision.decode('utf-8')
        except:
            revision = u''
        try:
            tag = tag.decode('utf-8')
        except:
            tag = u''
        try:
            tag_version = int(tag_version)
        except:
            tag_version = 0

    return KodiVersion


def get_plugin_url(queries):
    try:
        query = urllib.urlencode(queries)
    except UnicodeEncodeError:
        for k in queries:
            if isinstance(queries[k], unicode):
                queries[k] = queries[k].encode('utf-8')
        query = urllib.urlencode(queries)

    return sys.argv[0] + '?' + query


def end_of_directory(cache_to_disc=False):
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cache_to_disc)


def set_resolved_url(listitem, succeeded=True):
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), succeeded=succeeded, listitem=listitem)


def set_content(content):
    xbmcplugin.setContent(int(sys.argv[1]), content)


def create_item(item_dict, add=True):
    path = item_dict.get('path', '')
    path = path if isinstance(path, basestring) else get_plugin_url(path)
    list_item = ListItem(label=item_dict.get('label', ''), label2=item_dict.get('label2', ''), path=path)

    icon = get_icon()
    fanart = get_fanart()
    art = item_dict.get('art', {'icon': icon, 'thumb': icon, 'fanart': fanart})
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
    is_folder = not is_playable

    list_item.setProperty('isPlayable', str(is_playable).lower())

    url = path if isinstance(path, basestring) else get_plugin_url(path)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, list_item, isFolder=is_folder, totalItems=item_dict.get('total_items', 0))


def parse_query(query):
    q = {'mode': 'main'}
    if query.startswith('?'): query = query[1:]
    queries = urlparse.parse_qs(query)
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
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_GENRE)


def refresh_container():
    xbmc.executebuiltin('Container.Refresh')


def update_container(url):
    xbmc.executebuiltin('Container.Update(%s)' % url)


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
            return addon.getLocalizedString(self.strings[string_id]).encode('utf-8', 'ignore')
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

    def __init__(self, heading, line1='', line2='', line3='', background=False, active=True, timer=0):
        self.begin = time.time()
        self.timer = timer
        self.background = background
        self.heading = heading
        if active and not timer:
            self.pd = self.__create_dialog(line1, line2, line3)
            self.pd.update(0)

    def __create_dialog(self, line1, line2, line3):
        if self.background:
            pd = xbmcgui.DialogProgressBG()
            msg = line1 + line2 + line3
            pd.create(self.heading, msg)
        else:
            pd = xbmcgui.DialogProgress()
            pd.create(self.heading, line1, line2, line3)
        return pd

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

    def update(self, percent, line1='', line2='', line3=''):
        if self.pd is None and self.timer and (time.time() - self.begin) >= self.timer:
            self.pd = self.__create_dialog(line1, line2, line3)

        if self.pd is not None:
            if self.background:
                msg = line1 + line2 + line3
                self.pd.update(percent, self.heading, msg)
            else:
                self.pd.update(percent, line1, line2, line3)


class CountdownDialog(object):
    __INTERVALS = 5
    pd = None

    def __init__(self, heading, line1='', line2='', line3='', active=True, countdown=60, interval=5):
        self.heading = heading
        self.countdown = countdown
        self.interval = interval
        self.line3 = line3
        if active:
            pd = xbmcgui.DialogProgress()
            if not self.line3: line3 = 'Expires in: %s seconds' % countdown
            pd.create(self.heading, line1, line2, line3)
            pd.update(100)
            self.pd = pd

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

    def update(self, percent, line1='', line2='', line3=''):
        if self.pd is not None:
            self.pd.update(percent, line1, line2, line3)


class ListItem(xbmcgui.ListItem):
    def setArt(self, dictionary):
        if get_kodi_version().major < 16 and 'icon' in dictionary:
            self.setIconImage(dictionary['icon'])
            del dictionary['icon']
        super(ListItem, self).setArt(dictionary)
