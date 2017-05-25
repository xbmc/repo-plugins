# -*- coding: utf-8 -*-

"""
    LiveLite Add-on
    Author: Twilight0

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

import re, os, sys
import urlparse, random, urllib2
import xbmcaddon, xbmcgui, xbmcplugin, xbmc
from resources.lib import ordereddict

try:
    import YDStreamExtractor
except ImportError:
    pass

try:
    import urlresolver
except ImportError:
    pass

addon = xbmcaddon.Addon()
localisedstr = addon.getLocalizedString
addonname = addon.getAddonInfo("name")
addonpath = addon.getAddonInfo("path").decode('utf-8')
addonfanart = addon.getAddonInfo("fanart")
addonicon = addon.getAddonInfo("icon")
addonid = addon.getAddonInfo("id")

dialog = xbmcgui.Dialog()

addDirItems = xbmcplugin.addDirectoryItems
addDirItem = xbmcplugin.addDirectoryItem
endDir = xbmcplugin.endOfDirectory

execute = xbmc.executebuiltin

join = os.path.join
addonmedia = join(addonpath, 'resources', 'media')

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])
params = dict(urlparse.parse_qsl(sys.argv[2][1:]))
action = params.get('action', None)


def randomagent():

    BR_VERS = [
        ['%s.0' % i for i in xrange(18, 43)],
        ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111',
         '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111',
         '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124',
         '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71',
         '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'],
        ['11.0']]
    WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1',
                'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
    FEATURES = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
    RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
                'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
                'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko']
    index = random.randrange(len(RAND_UAS))
    return RAND_UAS[index].format(win_ver=random.choice(WIN_VERS), feature=random.choice(FEATURES),
                                  br_ver=random.choice(BR_VERS[index]))


def opener(url):

    req = urllib2.Request(url)
    req.add_header('User-Agent', randomagent())
    response = urllib2.urlopen(req)
    result = response.read()
    response.close()

    return result


def constructor():

    compiled_list = []
    groups = []

    if addon.getSetting('local_or_remote') == '0':
        with open (addon.getSetting('local')) as _file_:
            text = _file_.read()
            _file_.close()
    else:
        text = opener(addon.getSetting('remote'))

    result = text.replace('\r\n', '\n')
    items = re.compile('EXTINF:-?[0-9](,| |.*?)#', re.U + re.S).findall(result + '\n#')

    for item in items:

        title = re.findall('(,.*?)\\n', item, re.UNICODE)[0].rpartition(',')[2].decode('utf-8')
        link = re.findall('\\n(.*?)\\n', item, re.U)[0]
        icon = ''
        group = ''

        if 'tvg-logo' in item:
            icon = re.findall('tvg-logo="(.*?)"', item)[0]
        if 'icon' in item:
            icon = re.findall('icon="(.*?)"', item)[0]
        if 'group-title' in item:
            group = re.findall('group-title="(.*?)"', item, re.U)[0]

        item_data = ({'title': title, 'icon': addonicon if icon == '' else icon, 'group': 'NULL' if group == '' else group.decode('utf-8'), 'url': link})
        compiled_list.append(item_data)
        groups.append(group.decode('utf-8'))

    trimmed_groups = list(ordereddict.OrderedDict.fromkeys(groups))

    if len(trimmed_groups) == 1:
        addon.setSetting('group', 'ALL')

    if not text.startswith('#EXTM3U'):
        return
    else:
        return compiled_list, trimmed_groups


def switcher():

    groups = [localisedstr(30016)] + constructor()[1]

    choices = dialog.select(heading=localisedstr(30017), list=groups)

    if choices == 0:
        addon.setSetting('group', 'ALL')
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 1:
        addon.setSetting('group', (groups.pop(1)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 2:
        addon.setSetting('group', (groups.pop(2)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 3:
        addon.setSetting('group', (groups.pop(3)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 4:
        addon.setSetting('group', (groups.pop(4)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 5:
        addon.setSetting('group', (groups.pop(5)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 6:
        addon.setSetting('group', (groups.pop(6)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 7:
        addon.setSetting('group', (groups.pop(7)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 8:
        addon.setSetting('group', (groups.pop(8)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 9:
        addon.setSetting('group', (groups.pop(9)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 10:
        addon.setSetting('group', (groups.pop(10)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 11:
        addon.setSetting('group', (groups.pop(11)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 12:
        addon.setSetting('group', (groups.pop(12)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 13:
        addon.setSetting('group', (groups.pop(13)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 14:
        addon.setSetting('group', (groups.pop(14)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 15:
        addon.setSetting('group', (groups.pop(15)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 16:
        addon.setSetting('group', (groups.pop(16)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 17:
        addon.setSetting('group', (groups.pop(17)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 18:
        addon.setSetting('group', (groups.pop(18)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 19:
        addon.setSetting('group', (groups.pop(19)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 20:
        addon.setSetting('group', (groups.pop(20)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 21:
        addon.setSetting('group', (groups.pop(21)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 22:
        addon.setSetting('group', (groups.pop(22)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 23:
        addon.setSetting('group', (groups.pop(23)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 24:
        addon.setSetting('group', (groups.pop(24)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 25:
        addon.setSetting('group', (groups.pop(25)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 26:
        addon.setSetting('group', (groups.pop(26)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 27:
        addon.setSetting('group', (groups.pop(27)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 28:
        addon.setSetting('group', (groups.pop(28)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 29:
        addon.setSetting('group', (groups.pop(29)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 30:
        addon.setSetting('group', (groups.pop(30)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 31:
        addon.setSetting('group', (groups.pop(31)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 32:
        addon.setSetting('group', (groups.pop(32)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 33:
        addon.setSetting('group', (groups.pop(33)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 34:
        addon.setSetting('group', (groups.pop(34)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 35:
        addon.setSetting('group', (groups.pop(35)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 36:
        addon.setSetting('group', (groups.pop(36)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 37:
        addon.setSetting('group', (groups.pop(37)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 38:
        addon.setSetting('group', (groups.pop(38)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 39:
        addon.setSetting('group', (groups.pop(39)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 40:
        addon.setSetting('group', (groups.pop(40)))
        execute('Dialog.Close(busydialog)')
        execute('Container.Refresh')
    elif choices == 41:
        addon.setSetting('group', (groups.pop(41)))
        execute('Dialog.Close(busydialog)')
        execute('Container.Refresh')
    elif choices == 42:
        addon.setSetting('group', (groups.pop(42)))
        execute('Dialog.Close(busydialog)')
        execute('Container.Refresh')
    elif choices == 43:
        addon.setSetting('group', (groups.pop(43)))
        execute('Dialog.Close(busydialog)')
        execute('Container.Refresh')
    elif choices == 44:
        addon.setSetting('group', (groups.pop(44)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 45:
        addon.setSetting('group', (groups.pop(45)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 46:
        addon.setSetting('group', (groups.pop(46)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 47:
        addon.setSetting('group', (groups.pop(47)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 48:
        addon.setSetting('group', (groups.pop(48)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 49:
        addon.setSetting('group', (groups.pop(49)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 50:
        addon.setSetting('group', (groups.pop(50)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 51:
        addon.setSetting('group', (groups.pop(51)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 52:
        addon.setSetting('group', (groups.pop(52)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 53:
        addon.setSetting('group', (groups.pop(53)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 54:
        addon.setSetting('group', (groups.pop(54)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 55:
        addon.setSetting('group', (groups.pop(55)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 56:
        addon.setSetting('group', (groups.pop(56)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 55:
        addon.setSetting('group', (groups.pop(57)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 58:
        addon.setSetting('group', (groups.pop(58)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 59:
        addon.setSetting('group', (groups.pop(59)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 60:
        addon.setSetting('group', (groups.pop(60)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 61:
        addon.setSetting('group', (groups.pop(61)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 62:
        addon.setSetting('group', (groups.pop(62)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 63:
        addon.setSetting('group', (groups.pop(63)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 64:
        addon.setSetting('group', (groups.pop(64)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 65:
        addon.setSetting('group', (groups.pop(65)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 66:
        addon.setSetting('group', (groups.pop(66)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 67:
        addon.setSetting('group', (groups.pop(67)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 68:
        addon.setSetting('group', (groups.pop(68)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 69:
        addon.setSetting('group', (groups.pop(69)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 70:
        addon.setSetting('group', (groups.pop(70)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 71:
        addon.setSetting('group', (groups.pop(71)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 72:
        addon.setSetting('group', (groups.pop(72)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 73:
        addon.setSetting('group', (groups.pop(73)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 74:
        addon.setSetting('group', (groups.pop(74)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    elif choices == 75:
        addon.setSetting('group', (groups.pop(75)))
        execute('Dialog.Close(busydialog)')
        xbmc.sleep(500)
        execute('Container.Refresh')
    else:
        execute('Dialog.Close(busydialog)')
        dialog.notification(heading=addonname, message=localisedstr(30019), icon=addonicon, sound=False)


def list_items():

    item_list = []

    root_menu = [
        {
            'title': localisedstr(30011),
            'icon': join(addonmedia, 'settings.png'),
            'url': '{0}?action={1}'.format(addon_url, 'settings')
        }
        ,
        {
            'title': localisedstr(30015).format(localisedstr(30016) if addon.getSetting('group') == 'ALL' else addon.getSetting('group').decode('utf-8')),
            'icon': join(addonmedia, 'switcher.png'),
            'url': '{0}?action={1}'.format(addon_url, 'switcher')
        }
    ]

    null = [
        {
            'title': localisedstr(30013),
            'icon': join(addonmedia, 'null.png'),
            'url': addon_url
        }
    ]

    try:
        if not constructor()[0] == []:
            filtered = [item for item in constructor()[0] if any(item['group'] == selected for selected in [addon.getSetting('group').decode('utf-8')])] if not addon.getSetting('group') == 'ALL' else constructor()[0]
            if len(constructor()[1]) == 1:
                del root_menu[1]
            items = root_menu + filtered
        else:
            items = root_menu + null
            del items[1]
    except ValueError:
        items = root_menu + null
        del items[1]

    for item in items:

        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setInfo('video', {'title': item['title']})
        list_item.setArt({'icon': item['icon'], 'thumb': item['icon'], 'fanart': addonfanart})
        list_item.setProperty('IsPlayable', 'false') if item['icon'].endswith(('settings.png', 'switcher.png', 'null.png')) else list_item.setProperty('IsPlayable', 'true')
        list_item.addContextMenuItems([(localisedstr(30012), 'RunPlugin({0}?action=refresh)'.format(addon_url))])
        if addon.getSetting('youtube') == 'true' and item['url'].startswith('plugin://plugin.video.youtube/play/?video_id='):
            _url_ = '{0}?action=play&url={1}'.format(addon_url, item['url'])
            isFolder = False
        elif addon.getSetting('youtube') == 'false' and item['url'].startswith('plugin://plugin.video.youtube/play/?video_id='):
            _url_ = item['url']
            isFolder = False
        elif item['url'].startswith('plugin://'):
            _url_ = item['url']
            isFolder = False
        else:
            _url_ = '{0}?action=play&url={1}'.format(addon_url, item['url'])
            isFolder = False
        item_list.append((_url_, list_item, isFolder))

    addDirItems(addon_handle, item_list)
    endDir(addon_handle)


def play_item(path):

    list_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=list_item)


if action is None:

    list_items()

elif action == 'play':

    if params['url'].startswith('plugin://plugin.video.youtube/play/?video_id='):
        execute('PlayMedia("{0}")'.format(params['url']))
    else:
        try:
            stream = YDStreamExtractor.getVideoInfo(params['url'])
            url = stream.streamURL()
            # title = stream.selectedStream()['title']
            # icon = stream.selectedStream()['thumbnail']
            play_item(url)
        except AttributeError:
            try:
                if urlresolver.HostedMediaFile(params['url']).valid_url():
                    url = urlresolver.resolve(params['url'])
                    play_item(url)
                else:
                    play_item(params['url'])
            except NameError:
                play_item(params['url'])
        except NameError:
            try:
                if urlresolver.HostedMediaFile(params['url']).valid_url():
                    url = urlresolver.resolve(params['url'])
                    play_item(url)
                else:
                    play_item(params['url'])
            except NameError:
                play_item(params['url'])

elif action == 'install_youtube-dl':

    try:
        execute('RunPlugin(plugin://script.module.youtube.dl)')
    except:
        pass

elif action == 'install_urlresolver':

    try:
        execute('RunPlugin(plugin://script.module.urlresolver)')
    except Exception:
        pass

elif action == 'settings':

    execute('Dialog.Close(busydialog)')
    addon.openSettings()

elif action == 'refresh':

    execute('Container.Refresh')

elif action == 'switcher':
    dialog.notification(heading=addonname, message=localisedstr(30020), time=1500, sound=False)
    execute('ActivateWindow(busydialog)')
    switcher()
