#
#      Copyright (C) 2012 David Gray (N3MIS15)
#      N3MIS15@gmail.com
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
#  along with this Program; see the file LICENSE.txt. If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import sys
import urllib2
import urlparse
import string

import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs

from BeautifulSoup import BeautifulSoup
import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()


base_url = 'http://www.screwattack.com'
shows = [
    {'title': 30000, 'param': 'sidescrollers=0'},
    {'title': 30001, 'param': 'death-battle=0'},
    {'title': 30002, 'param': 'clip-week=0'},
    {'title': 30003, 'param': 'hard-news=0'},
    {'title': 30004, 'param': 'Top-10s=0'},
    {'title': 30005, 'param': 'out-box=0'},
    {'title': 30006, 'param': 'best-ever=0'},
    {'title': 30007, 'param': 'screwin-around=0'},
    {'title': 30008, 'param': 'random-awesomeness=0'},
    {'title': 30009, 'param': 'Cinemassacre=0'},
]


def screwattack_home():
    for show in shows:
        item = xbmcgui.ListItem(addon.getLocalizedString(show['title']), iconImage=icon)
        item.setProperty('Fanart_Image', fanart)

        url = '%s?%s' % (path, show['param'])
        xbmcplugin.addDirectoryItem(num, url, item, True)

    xbmcplugin.setContent(num, 'episodes')
    xbmcplugin.endOfDirectory(num)


def screwattack_episodes(show, page='0'):
    url = '%s/user/%s/videos?page=%s' % (base_url, show, page)
    soup = BeautifulSoup(urllib2.urlopen(url), convertEntities=BeautifulSoup.HTML_ENTITIES)

    content = soup.find('div', id="content")
    field = content.findAll('span', 'field-content')

    for f in field:
        atag = f.find('h2', 'title').a
        href = atag['href']
        title = atag.string
        try:
            img = f.find('a', 'imagecache').img['src']
        except:
            img = icon
        plot = f.find('div', 'info').string

        url = '%s?video=%s&show=%s&title=%s&img=%s' % (path, href, show, title, img)

        item = xbmcgui.ListItem(title, thumbnailImage=img)
        item.setInfo('Video', {'Title': title, 'Plot': plot})
        item.setProperty('Fanart_Image', fanart)

        item.addContextMenuItems([(addon.getLocalizedString(39900), 'XBMC.RunPlugin(%s&download=true)' % url)])
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(num, url, item, False)


    if content.find('li', 'pager-next').a:
        item = xbmcgui.ListItem(addon.getLocalizedString(30010), iconImage=icon)
        item.setProperty('Fanart_Image', fanart)

        url = '%s?%s=%s' % (path, show, int(page)+1)
        xbmcplugin.addDirectoryItem(num, url, item, True)

    xbmcplugin.setContent(num, 'episodes')
    xbmcplugin.endOfDirectory(num)


def screwattack_open(url, show, title=None, img=None, download=False):
    url = urllib2.urlopen(base_url+url)
    soup = BeautifulSoup(url)
    unique = None
    video = None

    try:
        src = soup.iframe['src']

        if 'youtube' in src:
            x = src.find('embed/') + 6
            y = src.find('?')
            video = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + src[x:y]
            unique = True
        else:
            _id = soup.iframe['id']
            x = _id.find('_') + 1
            unique = _id[x:]
    except:
        pass

    if not unique:
        try:
            _id = soup.find('object').find('param')['value'][:-1]
            x = _id.rfind('/') + 1
            unique = _id[x:]
        except:
            screwattack_popup(90000, 90001)
            return

    if not video:
        video = 'http://screwattack.springboardplatform.com/storage/screwattack.com/conversion/%s.mp4' % unique

    if download:
        screwattack_download(video, title, show)
    else:

        item = xbmcgui.ListItem(label=title, thumbnailImage=img, path=video)
        item.setInfo(type='Video', infoLabels={'Title': title.title()})
        xbmcplugin.setResolvedUrl(handle=num, succeeded=True, listitem=item)

    return


def screwattack_download(url, title, showname):
    if addon.getSetting('download_path'):
        download_path = addon.getSetting('download_path')
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        title = ''.join(c for c in title if c in valid_chars)

        if addon.getSetting('use_show_path'):
            for show in shows:

                if show['param'][:-2] == showname:
                    download_path = os.path.join(download_path, ''.join(c for c in addon.getLocalizedString(show['title']) if c in valid_chars))
                    if not xbmcvfs.exists(download_path):
                        xbmcvfs.mkdir(download_path)

                    break

        downloader.download(title+'.mp4', {'url': url, 'Title': title, 'download_path': download_path})

    else:
        screwattack_popup(90010, 90011)


def screwattack_popup(heading, line1):
    heading = addon.getLocalizedString(heading)
    line1 = addon.getLocalizedString(line1)
    xbmcgui.Dialog().ok(heading, line1)


if __name__ == '__main__':
    addon = xbmcaddon.Addon(id='plugin.video.screwattack')
    path = sys.argv[0]
    params = urlparse.parse_qs(sys.argv[2][1:])
    num = int(sys.argv[1])
    icon = os.path.join(addon.getAddonInfo('path'), 'icon.png')
    fanart = os.path.join(addon.getAddonInfo('path'), 'fanart.jpg')

    if params.keys():
        if not 'video' in params:
            screwattack_episodes(params.keys()[0], params[params.keys()[0]][0])

        else:
            vid_params = {
                'url': params['video'][0],
                'show': params['show'][0],
                'title': params['title'][0],
                'img': params['img'][0]
            }

            if 'download' in params:
                vid_params['download'] = True

            screwattack_open(**vid_params)

    else:
        screwattack_home()

