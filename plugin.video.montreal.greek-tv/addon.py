# -*- coding: utf-8 -*-

"""
    Montreal Greek TV Add-on
    Author: greektimes

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

import requests, json, re
from CommonFunctions import parseDOM
from base64 import b64decode
from resources.lib import control, youtube, cache, directory
from resources.lib.init import syshandle, action, url
from resources.lib.compat import range


def yt():

    # Please do not copy these keys, instead create your own:
    # http://forum.kodi.tv/showthread.php?tid=267160&pid=2299960#pid2299960

    key = 'QUl6YVN5QThrMU95TEdmMDNIQk5sMGJ5RDUxMWpyOWNGV28yR1I0'
    cid = 'UCFr8nqHDhA_fLQq2lEK3Mlw'

    return youtube.youtube(key=b64decode(key)).videos(cid)


def vod():

    video_list = cache.get(yt, 12)

    for v in video_list:
        v.update({'action': 'play', 'isFolder': 'False'})

    directory.add(video_list)


def _news_index():

    base_link = 'https://issuu.com/greektimes/docs/'
    json_obj = 'https://issuu.com/call/profile_demo/v1/documents/greektimes?offset=0&limit=1000'

    result = requests.get(json_obj).text

    news_list = json.loads(result)['items']

    menu = []

    for n in news_list:

        title = n['title']
        image = n['coverUrl']
        url = base_link + n['uri']

        data = {'title': title, 'image': image, 'url': url, 'action': 'paper_index'}

        menu.append(data)

    return menu


def news_index():

    menu = cache.get(_news_index, 12)

    if menu is None:
        return

    directory.add(menu, content='images')


def _paper_index(link):

    base_img_url = 'https://image.isu.pub/'

    html = requests.get(link).text

    script = parseDOM(html, 'script', attrs={'type': 'application/javascript'})[-2]

    data = json.loads(script.partition(' = ')[2].rstrip(';'))
    document = data['document']
    total_pages = int(document['pageCount'])

    menu = []

    for page in list(range(1, total_pages + 1)):

        title = document['title'] + ' - ' + control.lang(30003) + ' ' + str(page)
        page_img = base_img_url + document['id'] + '/jpg/page_{0}_thumb_large.jpg'.format(str(page))
        page_url = base_img_url + document['id'] + '/jpg/page_{0}.jpg'.format(str(page))

        data = {'title': title, 'image': page_img, 'url': page_url}

        menu.append(data)

    return menu


def paper_index(link):

    menu = []

    items = cache.get(_paper_index, 12, link)

    if items is None:
        return

    for i in items:
        li = control.item(label=i['title'])
        li.setArt(
            {
                'poster': i['image'], 'thumb': i['image'],
                'fanart': control.join(control.addonPath, 'resources', 'media', 'newspaper_fanart.png')
            }
        )
        li.setInfo('image', {'title': i['title'], 'picturepath': i['url']})
        url = i['url']
        menu.append((url, li, False))

    control.content(syshandle, 'images')
    control.addItems(syshandle, menu)
    control.directory(syshandle)


def _podcasts():

    menu = []

    feed_url = 'http://greektimes.ca/feed/podcast/'

    xml = requests.get(feed_url).text

    items = parseDOM(xml, 'item')

    for item in items:

        title = parseDOM(item, 'title')[0]
        uri = parseDOM(item, 'enclosure', attrs={'type': 'audio/mpeg'}, ret='url')[0]
        fanart = parseDOM(item, 'enclosure', attrs={'type': 'image/(?:jpeg|png)'}, ret='url')[0]
        image = parseDOM(item, 'img', attrs={'class': '.*?wp-image-\d{1,4}.*?'}, ret='srcset')[0]
        img_urls = image.split(',')
        image = [
            i.rpartition(' ')[0].strip() for i in img_urls if int(i[-5:-1]) == min([int(v[-5:-1]) for v in img_urls])
        ][0]
        comment = parseDOM(item, 'description')[0]
        year = int(re.search('(\d{4})', parseDOM(item, 'pubDate')[0]).group(1))

        data = {
            'title': title, 'url': uri, 'image': image, 'fanart': fanart, 'comment': comment, 'lyrics': comment,
            'year': year
        }

        menu.append(data)

    return menu


def podcasts():

    items = cache.get(_podcasts, 6)

    if items is None:
        return

    for i in items:
        i.update({'action': 'play', 'isFolder': 'False'})

    directory.add(items, content='music')


def main_menu():

    xml = requests.get(url='http://s135598769.onlinehome.us/mgtv.xml').text

    mgtv = parseDOM(xml, 'title')[0]
    livetv_url = parseDOM(xml, 'url')[0]
    mgr = parseDOM(xml, 'title')[1]
    radio_url = parseDOM(xml, 'url')[1]

    menu = [
        {
            'title': mgtv.replace('Live', control.lang(30004)),
            'action': 'play',
            'url': livetv_url,
            'icon': 'livetv.png',
            'isFolder': 'False'
        }
        ,
        {
            'title': mgr.replace('Live', control.lang(30004)),
            'action': 'play',
            'url': radio_url,
            'icon': 'radio.png',
            'isFolder': 'False'
        }
        ,
        {
            'title': 'Montreal Greek TV - {0}'.format(control.lang(30001).encode('utf-8')),
            'action': 'youtube',
            'icon': 'youtube.png'
        }
        ,
        {
            'title': control.lang(30002),
            'action': 'news_addon',
            'icon': 'newspaper_icon.png',
            'fanart': 'xronika_fanart.png'
        }
        ,
        {
            'title': 'Montreal Greek TV - {0}'.format(control.lang(30005)),
            'action': 'audio_addon',
            'icon': 'pod_icon.jpg',
            'fanart': 'pod_fanart.jpg'
        }
    ]

    for item in menu:
        cache_clear = {'title': 30006, 'query': {'action': 'cache_clear'}}
        item.update({'cm': [cache_clear]})

    directory.add(menu)


def play_item(path):

    directory.resolve(path)


if action is None:

    fp = control.infoLabel('Container.FolderPath')

    if 'image' in fp:
        news_index()
    elif 'audio' in fp:
        podcasts()
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

elif action == 'audio_addon':

    control.execute('ActivateWindow(music,"plugin://{0}/?content_type=audio",return)'.format(control.addonInfo('id')))

elif action == 'cache_clear':

    cache.clear(withyes=False)

else:
    import sys
    sys.exit()
