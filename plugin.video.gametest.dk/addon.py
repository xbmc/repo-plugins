import re
import os
import sys

import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web
import danishaddons.info

BASE_URL = 'http://www.gametest.dk/'
FLV_URL = BASE_URL + 'gametesttest/reviews/%s/%s.flv'
REVIEWS_URL = BASE_URL + 'index.php?anmeldelser=alle'
PAGE_URL = BASE_URL + 'index.php?page=%s'

CATEGORIES = [
    {'title' : 30010, 'params' : 'reviews'},
    {'title' : 30011, 'params' : 'retro'},
    {'title' : 30012, 'params' : 'stunts'},
]

def showOverview():
    html = danishaddons.web.downloadAndCacheUrl(BASE_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'overview.html'), 24 * 60)

    m = re.search('Sendt den ([^<]+).*?<ul>(.*?)</ul>', html, re.DOTALL)
    date = m.group(1)
    title = danishaddons.msg(30000) % date
    games = m.group(2).replace('<li>', '').replace('</li>', '\n')

    path = danishaddons.ADDON.getAddonInfo('path')
    icon = os.path.join(path, 'icon.png')
    item = xbmcgui.ListItem(title, iconImage = icon)
    item.setInfo('video', {
        'title' : title,
        'plot' : str(danishaddons.msg(30001)) + games,
        'date' : date.replace('-', '.')
    })
    url = FLV_URL % ('file', 'Programmet')
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    for idx, c in enumerate(CATEGORIES):
        item = xbmcgui.ListItem(danishaddons.msg(c['title']), iconImage = icon)
        url = danishaddons.ADDON_PATH + '?' + c['params']
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, True)

    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'episodes')
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def showReviews():
    html = danishaddons.web.downloadAndCacheUrl(REVIEWS_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'reviews.html'), 24 * 60)

    for m in re.finditer("index.php\?play=(.*?)&type=anmeldelse'><img src=' (.*?)'.*?anmeldelse'>(.*?)</a>.*?af: (.*?)</a>(.*?)time'>(.*?)</p>", html, re.DOTALL):
        slug = m.group(1)
        icon = m.group(2)
        title = m.group(3)
        author = m.group(4)
        rating = m.group(5).count('good.png')
        date = m.group(6)

        item = xbmcgui.ListItem(title, iconImage = BASE_URL + icon)
        item.setInfo('video', {
            'title' : title,
            'date' : date.replace('-', '.'),
            'year' : int(date[6:]),
            'credits' : author,
            'plot' : title,
            'rating' : rating
        })
        url = FLV_URL % ('file', slug)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'episodes')
    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def showPage(page):
    html = danishaddons.web.downloadAndCacheUrl(PAGE_URL % page, os.path.join(danishaddons.ADDON_DATA_PATH, '%s.html' % page), 24 * 60)

    for m in re.finditer("index.php\?play=(.*?)&type=.*?src=[ \"](.*?)[ \"](.*?<b>(.*?)</b>.*?af:.*?>(.*?)</a>)?", html, re.DOTALL):
        slug = m.group(1)
        icon = m.group(2)
        title = m.group(4)
        author = m.group(5)

        item = xbmcgui.ListItem(title, iconImage = BASE_URL + icon)
        item.setInfo('video', {
            'title' : title,
            'credits' : author,
            'plot' : title
        })

        url = FLV_URL % ('stunts', slug)
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item)

    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'episodes')
    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)



if __name__ == '__main__':
    danishaddons.init(sys.argv)

    if danishaddons.ADDON_PARAMS.has_key('reviews'):
        showReviews()
    elif danishaddons.ADDON_PARAMS.has_key('retro'):
        showPage('retro')
    elif danishaddons.ADDON_PARAMS.has_key('stunts'):
        showPage('stunts')
    else:
        showOverview()

