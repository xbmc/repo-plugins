# -*- coding: utf-8 -*-

'''
    Tulip routine libraries, based on lambda's lamlib
    Author Twilight0

        License summary below, for more details please read license.txt file

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 2 of the License, or
        (at your option) any later version.
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import urllib
import control
from __init__ import sysaddon, syshandle


def add(items, cacheToDisc=True, content=None, mediatype=None, infotype='video'):

    if items is None or len(items) == 0:
        return

    sysicon = control.join(control.addonInfo('path'), 'resources', 'media')
    sysimage = control.addonInfo('icon')
    sysfanart = control.addonInfo('fanart')

    for i in items:
        try:
            try:
                label = control.lang(i['title']).encode('utf-8')
            except:
                label = i['title']

            if 'label' in i and not i['label'] == '0':
                label = i['label']

            if 'image' in i and not i['image'] == '0':
                image = i['image']
            elif 'poster' in i and not i['poster'] == '0':
                image = i['poster']
            elif 'icon' in i and not i['icon'] == '0':
                image = control.join(sysicon, i['icon'])
            else:
                image = sysimage

            if 'banner' in i and not i['banner'] == '0':
                banner = i['banner']
            elif 'fanart' in i and not i['fanart'] == '0':
                banner = i['fanart']
            else:
                banner = image

            fanart = i['fanart'] if 'fanart' in i and not i['fanart'] == '0' else sysfanart

            isFolder = False if 'isFolder' in i and not i['isFolder'] == '0' else True

            url = '%s?action=%s' % (sysaddon, i['action'])

            try:
                url += '&url=%s' % urllib.quote_plus(i['url'])
            except:
                pass
            try:
                url += '&image=%s' % urllib.quote_plus(i['image'])
            except:
                pass

            cm = []
            menus = i['cm'] if 'cm' in i else []

            for menu in menus:
                try:
                    try:
                        tmenu = control.lang(menu['title']).encode('utf-8')
                    except:
                        tmenu = menu['title']
                    qmenu = urllib.urlencode(menu['query'])
                    cm.append((tmenu, 'RunPlugin(%s?%s)' % (sysaddon, qmenu)))
                except:
                    pass

            meta = dict((k, v) for k, v in i.iteritems() if not k == 'cm' and not v == '0')
            if not mediatype == None:
                meta['mediatype'] = mediatype

            item = control.item(label=label, iconImage=image, thumbnailImage=image)

            item.setArt({'icon': image, 'thumb': image, 'poster': image, 'tvshow.poster': image, 'season.poster': image, 'banner': banner, 'tvshow.banner': banner, 'season.banner': banner})

            item.setProperty('Fanart_Image', fanart)

            item.addContextMenuItems(cm)
            item.setInfo(type=infotype, infoLabels = meta)
            if isFolder == False:
                item.setProperty('IsPlayable', 'true') if not i['action'] == 'pvr_client' else item.setProperty('IsPlayable', 'false')

            control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
        except:
            pass

    try:
        i = items[0]
        if i['next'] == '':
            raise Exception()

        url = '%s?action=%s&url=%s' % (sysaddon, i['nextaction'], urllib.quote_plus(i['next']))
        icon = i['nexticon'] if 'nexticon' in i else control.join(sysicon, 'next.png')
        fanart = i['nextfanart'] if 'nextfanart' in i else sysfanart
        try:
            label = control.lang(i['nextlabel']).encode('utf-8')
        except:
            label = 'next'

        item = control.item(label=label, iconImage=icon, thumbnailImage=icon)
        item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'tvshow.poster': icon, 'season.poster': icon, 'banner': icon, 'tvshow.banner': icon, 'season.banner': icon})
        item.setProperty('Fanart_Image', fanart)
        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
    except:
        pass

    if not content is None:
        control.content(syshandle, content)

    control.directory(syshandle, cacheToDisc=cacheToDisc)


def resolve(url, meta=None, icon=None):

    item = control.item(path=url)

    if not icon is None:
        item.setArt({'icon': icon, 'thumb': icon})

    if not meta is None:
        item.setInfo(type='Video', infoLabels=meta)

    control.resolve(syshandle, True, item)
