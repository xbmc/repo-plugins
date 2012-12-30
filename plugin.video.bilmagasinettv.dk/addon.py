#
#      Copyright (C) 2012 Tommy Winther
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urllib2
import urlparse
import simplejson

import buggalo

import xbmcgui
import xbmcaddon
import xbmcplugin

BASE_URL = 'http://www.bilmagasinettv.dk'
API_URL = BASE_URL + '/api/'

class BilMagasinetTVAddon(object):
    def showAlbums(self):
        print API_URL + 'album/list?format=json'
        u = urllib2.urlopen(API_URL + 'album/list?format=json')
        data = u.read()
        u.close()
        json = simplejson.loads(data[data.index('{'):])

        for album in json['albums']:
            item = xbmcgui.ListItem(album['title'], iconImage = ICON)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?album=' + album['album_id'], item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showClips(self, album_id):
        u = urllib2.urlopen(API_URL + 'photo/list?format=json&album_id=' + album_id)
        data = u.read()
        u.close()
        json = simplejson.loads(data[data.index('{'):])

        for video in json['photos']:
            infoLabels = dict()
            infoLabels['studio'] = ADDON.getAddonInfo('name')
            infoLabels['plot'] = video['content_text']
            infoLabels['title'] = video['title']
            infoLabels['aired'] = video['publish_date_ansi'][0:10]
            infoLabels['year'] = int(video['publish_date_ansi'][0:4])

            item = xbmcgui.ListItem(video['title'], iconImage = BASE_URL + video['large_download'], thumbnailImage = BASE_URL + video['large_download'])
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', BASE_URL + video['large_download'])
            xbmcplugin.addDirectoryItem(HANDLE, BASE_URL + video['video_hd_download'], item)

        xbmcplugin.endOfDirectory(HANDLE)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        bmtv = BilMagasinetTVAddon()
        if PARAMS.has_key('album'):
            bmtv.showClips(PARAMS['album'][0])
        else:
            bmtv.showAlbums()
    except Exception:
        buggalo.onExceptionRaised()
