import re
import os
import sys

import xbmcgui
import xbmcplugin

import simplejson
import danishaddons
import danishaddons.web

SHOWS_URL = 'http://videovideo.dk/shows/json/'
EPISODES_URL = 'http://videovideo.dk/episodes/json/show_id/%s'
RSS_URL_TEMPLATE = 'http://videovideo.dk/show/%s/rss/720/mp4'

def showOverview():
    json_path = os.path.join(danishaddons.ADDON_DATA_PATH, 'shows.json')
    json = danishaddons.web.downloadAndCacheUrl(SHOWS_URL, json_path, 24 * 60)

    shows = simplejson.loads(json)
    for show in shows:
        item = xbmcgui.ListItem(show['title'], iconImage = show['image'])
        item.setInfo(type = 'video', infoLabels = {
            'title' : show['title'],
            'plot' : show['description']
        })
        item.setProperty('Fanart_Image', show['imagefull'])

        m = re.search('([0-9]+)$', show['url'])
        show_id = m.group(1)
        
        url = danishaddons.ADDON_PATH + '?id=' + show_id
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, url, item, True)

    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)
    
def showShow(id):
    json_path = os.path.join(danishaddons.ADDON_DATA_PATH, 'episodes_%s.json' % id)
    json = danishaddons.web.downloadAndCacheUrl(EPISODES_URL % id, json_path, 24 * 60)

    episodes = simplejson.loads(json)
    for episode in episodes:
        item = xbmcgui.ListItem(episode['title'], iconImage = episode['image'])

        date = '%s.%s.%s' % (episode['timestamp'][8:10], episode['timestamp'][5:7], episode['timestamp'][0:4])

        infoLabels = {
            'title' : episode['title'],
            'plot' : episode['shownotes'],
            'date' : date,
            'aired' : episode['timestamp'][0:11],
            'year' : int(episode['timestamp'][0:4])
        }
        item.setInfo('video', infoLabels)
        item.setProperty('Fanart_Image', episode['imagefull'])
        xbmcplugin.addDirectoryItem(danishaddons.ADDON_HANDLE, episode['distributions']['720'], item, False)

    xbmcplugin.addSortMethod(danishaddons.ADDON_HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(danishaddons.ADDON_HANDLE)


if __name__ == '__main__':
    danishaddons.init(sys.argv)

    if danishaddons.ADDON_PARAMS.has_key('id'):
        showShow(danishaddons.ADDON_PARAMS['id'])
    else:
        showOverview()

