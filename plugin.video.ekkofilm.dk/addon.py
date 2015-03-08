#
#      Copyright (C) 2015 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urlparse
import re
import urllib2


import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import buggalo

BASE_URL = 'http://www.ekkofilm.dk'
VIDEO_URL = BASE_URL + '/shortlist/film/?o=alpha&page=%d'
FILM_URL = BASE_URL + '/shortlist/film/%s/'


def showOverview(page=1):
    u = urllib2.urlopen(VIDEO_URL % page)
    html = u.read()
    u.close()

    for m in re.finditer('class="still".*?src="([^"]+)">.*?href="/shortlist/film/([^/]+)/">([^<]+)</a>.*?class="director">([^<]+)<.*?class="teaser">([^<]+)<', html, re.DOTALL):
        image = BASE_URL + m.group(1)
        slug = m.group(2)
        title = m.group(3)
        director = m.group(4)
        teaser = m.group(5)

        if director.find(':') != -1:
            director = director[director.find(':')+1:].strip()

        item = xbmcgui.ListItem(title, iconImage=image)
        item.setProperty('Fanart_Image', image.replace('165x100', '1200x630'))
        item.setProperty('IsPlayable', 'true')
        item.setInfo(type='video', infoLabels={
            'title': title,
            'plot': teaser,
            'director': director,
            'studio': ADDON.getAddonInfo('name')
        })

        url = PATH + '?slug=' + slug
        xbmcplugin.addDirectoryItem(HANDLE, url, item)

    if html.find('page=%d' % (page + 1)) != -1:
        showOverview(page + 1)
        return

    xbmcplugin.endOfDirectory(HANDLE)


def playFilm(slug):
    u = urllib2.urlopen(FILM_URL % slug)
    html = u.read()
    u.close()

    m = re.search('<div class="title">.*?<h2>(.*?)</h2>.*?<a class="vignette" href="([^"]+)" data-type="video/mp4">.*?<video.*?poster="([^"]+)".*?<source src="([^"]+)" type=\'video/mp4\' data-res="HD" />', html, re.DOTALL)
    if m is not None:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        image = BASE_URL + m.group(3)
        # vignette
        url = BASE_URL + m.group(2)
        item = xbmcgui.ListItem(label=m.group(1), path=url, thumbnailImage=image)
        playlist.add(url, item)
        # film
        url = BASE_URL + m.group(4)
        playlist.add(url, xbmcgui.ListItem(label=m.group(1), path=url, thumbnailImage=image))

    else:
        item = xbmcgui.ListItem()
    xbmcplugin.setResolvedUrl(HANDLE, m is not None, item)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        if 'slug' in PARAMS:
            playFilm(PARAMS['slug'][0])
        else:
            showOverview()
    except:
        buggalo.onExceptionRaised()