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

import requests, json
import CommonFunctions as common
from base64 import b64decode
from resources.lib import control, youtube, cache, directory, syshandle, sysaddon, action, url, image


# Misc variables:
addonicon = control.addonInfo('icon')
addonart = control.join(control.addonPath, 'resources/media')
livetv_img = control.join(addonart, 'livetv.png')
radio_img = control.join(addonart, 'radio.png')
youtube_img = control.join(addonart, 'youtube.png')
news_icon = control.join(addonart, 'newspaper_icon.png')
news_fanart = control.join(addonart, 'newspaper_icon.png')
fp = control.infoLabel('Container.FolderPath')

# Please do not copy these keys, instead create your own:
# http://forum.kodi.tv/showthread.php?tid=267160&pid=2299960#pid2299960

key = b64decode('QUl6YVN5QThrMU95TEdmMDNIQk5sMGJ5RDUxMWpyOWNGV28yR1I0')
ytid = 'UCFr8nqHDhA_fLQq2lEK3Mlw'


def yt():

    return youtube.youtube(key=key).videos(ytid)


def vod():

    video_list = cache.get(yt, 12)

    print video_list

    for v in video_list:
        v.update({'action': 'play', 'isFolder': 'False'})

    directory.add(video_list)


def news_index():

    base_link = 'https://issuu.com/greektimes/docs/'
    json_obj = 'https://issuu.com/call/profile_demo/v1/documents/greektimes?offset=0&limit=1000'

    result = requests.get(json_obj).text

    news_list = json.loads(result)['items']

    empty_list = []

    for n in news_list:

        title = n['title']
        image = n['coverUrl']
        url = base_link + n['uri']

        data = {'title': title, 'image': image, 'url': url, 'action': 'paper_index'}

        empty_list.append(data)

    directory.add(empty_list, content='images')


def paper_index(link):

    base_img_url = 'https://image.isu.pub/'

    html = requests.get(link).text

    script = common.parseDOM(html, 'script', attrs={'type': 'application/javascript'})[-2]

    data = json.loads(script.partition(' = ')[2].rstrip(';'))
    document = data['document']
    total_pages = int(document['pageCount'])

    empty_list = []
    final_list = []

    for page in range(1, total_pages + 1):

        title = document['title'] + ' - ' + control.lang(30003) + ' ' + str(page)
        page_img = base_img_url + document['id'] + '/jpg/page_{0}_thumb_large.jpg'.format(str(page))
        page_url = base_img_url + document['id'] + '/jpg/page_{0}.jpg'.format(str(page))

        data = {'title': title, 'image': page_img, 'url': page_url}

        empty_list.append(data)

    for i in empty_list:
        li = control.item(label=i['title'])
        li.setArt({'poster': i['image'], 'thumb': i['image'], 'fanart': news_fanart})
        li.setInfo('image', {'title': i['title'], 'picturepath': i['url']})
        url = i['url']
        final_list.append((url, li, False))

    control.content(syshandle, 'images')
    control.addItems(syshandle, final_list)
    control.directory(syshandle)


def main_menu():

    xml = requests.get(url='http://s135598769.onlinehome.us/mgtv.xml').text

    mgtv = common.parseDOM(xml, 'title')[0]
    livetv_url = common.parseDOM(xml, 'url')[0]
    mgr = common.parseDOM(xml, 'title')[1]
    radio_url = common.parseDOM(xml, 'url')[1]

    # Live TV
    url1 = '{0}?action={1}&url={2}'.format(sysaddon, 'play', livetv_url)
    li1 = control.item(label=mgtv)
    li1.setArt({'icon': livetv_img, 'thumb': livetv_img, 'fanart': control.addonInfo('fanart')})
    li1.setInfo('video', {'title': mgtv})
    li1.setProperty('IsPlayable', 'true')
    control.addItem(handle=syshandle, url=url1, listitem=li1, isFolder=False)

    # Radio
    url2 = '{0}?action={1}&url={2}'.format(sysaddon, 'play', radio_url)
    li2 = control.item(label=mgr)
    li2.setArt({'icon': radio_img, 'thumb': radio_img, 'fanart': control.addonInfo('fanart')})
    li2.setInfo('audio', {'title': mgr})
    li2.setProperty('IsPlayable', 'true')
    control.addItem(handle=syshandle, url=url2, listitem=li2, isFolder=False)

    # Youtube
    url3 = '{0}?action={1}'.format(sysaddon, 'youtube')
    li3 = control.item(label='Montreal Greek TV - {0}'.format(control.lang(30001).encode('utf-8')))
    li3.setArt({'icon': youtube_img, 'thumb': youtube_img, 'fanart': control.addonInfo('fanart')})
    li3.setInfo('video', {'title': 'Montreal Greek TV - {0}'.format(control.lang(30001).encode('utf-8'))})
    control.addItem(handle=syshandle, url=url3, listitem=li3, isFolder=True)

    # Newspaper
    url4 = '{0}?action={1}'.format(sysaddon, 'news_addon')
    li4 = control.item(label='The Montreal Greek Times - {0}'.format(control.lang(30002).encode('utf-8')))
    li4.setArt({'icon': news_icon, 'thumb': news_icon, 'fanart': news_fanart})
    li4.setInfo('image', {'title': 'The Montreal Greek Times - {0}'.format(control.lang(30002).encode('utf-8')), 'picturepath': news_icon})
    control.addItem(handle=syshandle, url=url4, listitem=li4, isFolder=True)

    control.directory(syshandle)


def play_item(path):

    li = control.item(path=path)
    control.resolve(syshandle, True, listitem=li)


if action is None:

    if 'image' in fp:
        news_index()
    else:
        main_menu()

elif action == 'play':

    play_item(url)

elif action == 'youtube':

    vod()

elif action == 'news_index':

    news_index()

elif action == 'paper_index':

    paper_index(url)

elif action == 'news_addon':

    control.execute('ActivateWindow(pictures,"plugin://{0}/?content_type=image",return)'.format(control.addonInfo('id')))
