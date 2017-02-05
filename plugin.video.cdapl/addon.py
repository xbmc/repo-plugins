# coding: utf8
import json
import re
import sys
import urllib
import urllib2
import urlparse

import xbmc
import xbmcgui
import xbmcplugin

import bs4


__URL__ = sys.argv[0]
__HANDLE__ = int(sys.argv[1])
__QUERY__ = dict(urlparse.parse_qsl(sys.argv[2][1:]))


def fetch_video_details(cda_id, quality):
    url = 'http://m.cda.pl/video/{}?wersja={}'
    url = url.format(cda_id, quality)
    response = urllib2.urlopen(url)
    html = response.read()
    title = re.search('<title>([^<]+)', html).group(1)
    player_data = re.search("player_data='([^']+)", html).group(1)
    player_data = json.loads(player_data)
    return {
        'title': title,
        'url': player_data['video']['file'] + '.mp4',
        'poster_url': player_data['video']['poster'],
    }


def fetch_search_results(user_input):
    query = urllib.quote_plus(user_input)
    url_base = 'http://m.cda.pl/szukaj?q={}&gdzie=v&duration=dlugie&quality=all&s=best'
    url = url_base.format(query)
    response = urllib2.urlopen(url)
    html = response.read()
    items = []
    bs = bs4.BeautifulSoup(html, 'html.parser')
    results = bs.find_all('div', attrs={'class': 'box-elem'})
    for result in results:
        cda_id = result.find('a').attrs['href'].split('/')[-1]
        title = result.find('h2').text
        thumb = result.find('img').attrs['src']
        quality = result.find('span', attrs={'class': 'quality'})
        quality = quality.text if quality else ''
        duration = result.find('span', attrs={'class': 'timeElem'}).text
        h, m, s = duration.split(':')
        duration = int(h) * 3600 + int(m) * 60 + int(s)
        items.append((cda_id, title, thumb, quality, duration))
    return items


def play_video(cda_id, quality):
    video = fetch_video_details(cda_id, quality)
    # add some basic data
    li = xbmcgui.ListItem(video['title'], thumbnailImage=video['poster_url'])
    li.setInfo('video', {'Title': video['title']})
    xbmc.Player().play(video['url'], li)


def do_search():
    user_input = xbmcgui.Dialog().input('Wpisz tytuł filmu')
    if user_input == '':
        return

    search_results = fetch_search_results(user_input)

    if not search_results:
        xbmcgui.Dialog().ok('', 'Brak wyników dla: ' + user_input)
        return

    dir_items = []
    for cda_id, title, thumb, quality, duration in search_results:
        kodi_url = '{}?cda-id={}&quality={}'.format(
            __URL__,
            cda_id,
            quality,
        )
        li = xbmcgui.ListItem(label=title, thumbnailImage=thumb)
        li.setInfo('video', {'mediatype': 'movie'})
        li.setProperty("IsPlayable", "true")
        li.addStreamInfo('video', {'duration': duration})
        li.setArt({'icon': 'icon.png'})
        dir_items.append((kodi_url, li, False))
    xbmcplugin.addDirectoryItems(__HANDLE__, dir_items)

    xbmcplugin.addSortMethod(__HANDLE__, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(__HANDLE__)


def router():
    xbmcplugin.setContent(__HANDLE__, 'movies')

    # Home menu
    if __QUERY__ == {}:
        search_item = xbmcgui.ListItem(label='Szukaj...')
        xbmcplugin.addDirectoryItem(
            handle=__HANDLE__,
            url=__URL__ + '?search-dialog=1',
            listitem=search_item,
            isFolder=True
        )
        xbmcplugin.addSortMethod(__HANDLE__, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.endOfDirectory(__HANDLE__)
        return

    # Search dialog and results
    search_dialog = __QUERY__.get('search-dialog')
    if search_dialog:
        do_search()
        return

    # Play video
    cda_id = __QUERY__.get('cda-id')
    if cda_id:
        quality = __QUERY__.get('quality')
        play_video(cda_id, quality)
        return


router()
