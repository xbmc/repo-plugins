# -*- coding: utf-8 -*-

"""
    Montreal Greek TV Add-on
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

import requests
import CommonFunctions as common
from base64 import b64decode
from resources.lib import control, youtube, cache, directory, syshandle, sysaddon, action, url


# Misc variables:
addonicon = control.addonInfo('icon')
addonart = control.join(control.addonPath, 'resources/media')
livetv_img = control.join(addonart, 'livetv.png')
radio_img = control.join(addonart, 'radio.png')
youtube_img = control.join(addonart, 'youtube.png')
settings_img = control.join(addonart, 'settings.png')

# Please do not copy these keys, instead create your own:
# http://forum.kodi.tv/showthread.php?tid=267160&pid=2299960#pid2299960

key = b64decode('QUl6YVN5QThrMU95TEdmMDNIQk5sMGJ5RDUxMWpyOWNGV28yR1I0')
ytid = 'UCFr8nqHDhA_fLQq2lEK3Mlw'
old_radio_url = 'http://209.95.50.189:8049/stream'


def yt():
    return youtube.youtube(key=key).videos(ytid)


def vod():

    video_list = cache.get(yt, 12)

    print video_list

    for v in video_list:
        v.update({'action': 'play', 'isFolder': 'False'})

    directory.add(video_list)


def main_menu():

    xml = requests.get(url='http://www.greekradio.net/mgtv.xml').text

    mgtv = common.parseDOM(xml, 'title')[0]
    livetv_url = common.parseDOM(xml, 'url')[0]
    mgr = common.parseDOM(xml, 'title')[1]
    new_radio_url = common.parseDOM(xml, 'url')[1]

    # Live TV
    url1 = '{0}?action=play&url={1}'.format(sysaddon, livetv_url)
    li = control.item(label=mgtv)
    li.setArt({'icon': livetv_img, 'thumb': livetv_img, 'fanart': control.addonInfo('fanart')})
    li.setInfo('video', {'title': mgtv})
    li.setProperty('IsPlayable', 'true')
    control.addItem(handle=syshandle, url=url1, listitem=li, isFolder=False)

    # Radio
    url2 = '{0}?action=play&url={1}'.format(sysaddon, new_radio_url if control.setting('old-url') == 'false' else old_radio_url)
    li = control.item(label=mgr)
    li.setArt({'icon': radio_img, 'thumb': radio_img, 'fanart': control.addonInfo('fanart')})
    li.setInfo('audio', {'title': mgr})
    li.setProperty('IsPlayable', 'true')
    control.addItem(handle=syshandle, url=url2, listitem=li, isFolder=False)

    # Youtube
    url3 = '{0}?action=youtube'.format(sysaddon)
    li = control.item(label='Montreal Greek TV - Youtube Channel')
    li.setArt({'icon': youtube_img, 'thumb': youtube_img, 'fanart': control.addonInfo('fanart')})
    li.setInfo('video', {'title': 'Montreal Greek TV - Youtube Channel'})
    control.addItem(handle=syshandle, url=url3, listitem=li, isFolder=True)

    control.directory(syshandle)


def play_item(path):

    li = control.item(path=path)
    control.resolve(syshandle, True, listitem=li)


if action is None:

    main_menu()

elif action == 'play':

    play_item(url)

elif action == 'youtube':

    vod()

elif action == 'settings':

    control.openSettings()
