import os
import re
import sys
import simplejson

import xbmc
import xbmcgui
import xbmcplugin

import danishaddons
import danishaddons.web
import danishaddons.info

BASE_URL = 'http://www.dr.dk/Bonanza/'

def search():
    keyboard = xbmc.Keyboard('', danishaddons.msg(30001))
    keyboard.doModal()
    if keyboard.isConfirmed():
        html = danishaddons.web.downloadUrl('http://www.dr.dk/bonanza/search.htm?&type=video&limit=120&needle=' + keyboard.getText().replace(' ', '+')) # don't cache search results
        addContent(html)
        xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)
        xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'episodes')


def showCategories():
    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'tvshows')

    html = danishaddons.web.downloadAndCacheUrl(BASE_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'categories.html'), 24 * 60)
    icon = os.path.join(os.getcwd(), 'icon.png')

    item = xbmcgui.ListItem(danishaddons.msg(30001), iconImage = icon)
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?mode=search', item, True)
    item = xbmcgui.ListItem(danishaddons.msg(30002), iconImage = icon)
    xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, danishaddons.ADDON_PATH + '?mode=recommend', item, True)

    for m in re.finditer('<a href="(/Bonanza/kategori/.*\.htm)">(.*)</a>', html):
        path = m.group(1)
        title = m.group(2)

        item = xbmcgui.ListItem(title, iconImage = icon)
        item.setInfo(type = 'video', infoLabels = {
            'title' : title
        })
        url = danishaddons.ADDON_PATH + '?mode=subcat&url=http://www.dr.dk' + path + '&title=' + title
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, True)

    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)


def showRecommendations():
    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'tvshows')

    html = danishaddons.web.downloadAndCacheUrl(BASE_URL, os.path.join(danishaddons.ADDON_DATA_PATH, 'recommendations.html'), 24 * 60)

    # remove anything but 'Redaktionens favoritter'
    html = html[html.find('<span class="tabTitle">Redaktionens favoritter</span>'):]
    addSubCategories(html)
    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)


def showSubCategories(url, title):
    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'tvshows')

    html = danishaddons.web.downloadAndCacheUrl(url.replace(' ', '+'), os.path.join(danishaddons.ADDON_DATA_PATH, 'category-' + title + '.html'), 24 * 60)

    # remove 'Redaktionens favoritter' as they are located on every page
    html = html[:html.find('<span class="tabTitle">Redaktionens favoritter</span>')]

    addSubCategories(html)
    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)

def showContent(url, title):
    html = danishaddons.web.downloadAndCacheUrl(url, os.path.join(danishaddons.ADDON_DATA_PATH, 'content-' + title + '.html'), 60)
    addContent(html)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)
    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'episodes')



def addSubCategories(html):
    xbmcplugin.setContent(danishaddons.ADDON_HANDLE, 'tvshows')

    for m in re.finditer('<a href="(http://www\.dr\.dk/bonanza/serie/[^\.]+\.htm)"[^>]+>..<img src="(http://downol\.dr\.dk/download/bonanza/collectionThumbs/[^"]+)"[^>]+>..<b>([^<]+)</b>..<span>([^<]+)</span>..</a>', html, re.DOTALL):
        url = m.group(1)
        image = m.group(2)
        title = m.group(3)
        description = m.group(4)

        item = xbmcgui.ListItem(title, iconImage = image)
        item.setInfo(type = 'video', infoLabels = {
            'title' : title,
            'plot' : description
        })
        url = danishaddons.ADDON_PATH + '?mode=content&url=' + url + '&title=' + title
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, True)


def addContent(html):
    for m in re.finditer('newPlaylist\(([^"]+)"', html):
        raw = m.group(1)[:-2].replace('&quot;', '"')
        json = simplejson.loads(raw)

        infoLabels = {}
        if json['Title'] is not None:
            infoLabels['title'] = danishaddons.web.decodeHtmlEntities(json['Title'])
        if json['Description'] is not None:
            infoLabels['plot'] = danishaddons.web.decodeHtmlEntities(json['Description'])
        if json['Colophon'] is not None:
            infoLabels['writer'] = danishaddons.web.decodeHtmlEntities(json['Colophon'])
        if json['Actors'] is not None:
            infoLabels['cast'] = danishaddons.web.decodeHtmlEntities(json['Actors'])
        if json['Rating'] is not None:
            infoLabels['rating'] = json['Rating']
        if json['FirstPublished'] is not None:
            infoLabels['year'] = int(json['FirstPublished'][:4])
        if json['Duration'] is not None:
            infoLabels['duration'] = danishaddons.info.secondsToDuration(int(json['Duration']) / 1000)

        item = xbmcgui.ListItem(infoLabels['title'], iconImage = findFileLocation(json, 'Thumb'))
        item.setInfo('video', infoLabels)

        rtmp_url = findFileLocation(json, 'VideoHigh')
        if rtmp_url is None:
            rtmp_url = findFileLocation(json, 'VideoMid')
        if rtmp_url is None:
            rtmp_url = findFileLocation(json, 'VideoLow')

        # patch rtmp_url to work with mplayer
        m = re.match('(rtmp://.*?)/(.*)', rtmp_url)
        rtmp_url = '%s/bonanza/%s' % (m.group(1), m.group(2))
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, rtmp_url, item, False)



def findFileLocation(json, type):
    for file in json['Files']:
        if file['Type'] == type:
            return file['Location']
    return None


if __name__ == '__main__':
    danishaddons.init(sys.argv)
    
    if danishaddons.ADDON_PARAMS.has_key('mode') and danishaddons.ADDON_PARAMS['mode'] == 'subcat':
        showSubCategories(danishaddons.ADDON_PARAMS['url'], danishaddons.ADDON_PARAMS['title'])
    elif danishaddons.ADDON_PARAMS.has_key('mode') and danishaddons.ADDON_PARAMS['mode'] == 'content':
        showContent(danishaddons.ADDON_PARAMS['url'], danishaddons.ADDON_PARAMS['title'])
    elif danishaddons.ADDON_PARAMS.has_key('mode') and danishaddons.ADDON_PARAMS['mode'] == 'search':
        search()
    elif danishaddons.ADDON_PARAMS.has_key('mode') and danishaddons.ADDON_PARAMS['mode'] == 'recommend':
        showRecommendations()
    else:
        showCategories()

