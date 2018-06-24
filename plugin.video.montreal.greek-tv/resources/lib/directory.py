# -*- coding: utf-8 -*-

'''
    Montreal Greek TV Add-on
    Author: greektimes

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
from __future__ import absolute_import, division, unicode_literals

from resources.lib.compat import urlencode, quote_plus, iteritems
from resources.lib import control
from resources.lib.init import sysaddon, syshandle


def add(items, cacheToDisc=True, content=None, mediatype=None, infotype='video'):

    if items is None or len(items) == 0:
        return

    # sysicon = control.join(control.addonInfo('path'), 'resources', 'media')
    sysimage = control.addonInfo('icon')
    sysfanart = control.addonInfo('fanart')

    for i in items:

        try:
            label = control.lang(i['title']).encode('utf-8')
        except BaseException:
            label = i['title']

        if 'label' in i and not i['label'] == '0':
            label = i['label']

        if 'image' in i and not i['image'] == '0':
            image = i['image']
        elif 'poster' in i and not i['poster'] == '0':
            image = i['poster']
        elif 'icon' in i and not i['icon'] == '0':
            image = control.addonmedia(i['icon'])
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
            url += '&url=%s' % quote_plus(i['url'])
        except BaseException:
            pass
        try:
            url += '&title=%s' % quote_plus(i['title'])
        except KeyError:
            try:
                url += '&title=%s' % quote_plus(i['title'].encode('utf-8'))
            except KeyError:
                pass
        except BaseException:
            pass

        try:
            url += '&image=%s' % quote_plus(i['image'])
        except KeyError:
            try:
                url += '&image=%s' % quote_plus(i['image'].encode('utf-8'))
            except KeyError:
                pass
        except BaseException:
            pass
        try:
            url += '&name=%s' % quote_plus(i['name'])
        except KeyError:
            try:
                url += '&name=%s' % quote_plus(i['name'].encode('utf-8'))
            except KeyError:
                pass
        except BaseException:
            pass
        try:
            url += '&year=%s' % quote_plus(i['year'])
        except BaseException:
            pass
        try:
            url += '&plot=%s' % quote_plus(i['plot'])
        except KeyError:
            try:
                url += '&plot=%s' % quote_plus(i['plot'].encode('utf-8'))
            except KeyError:
                pass
        except BaseException:
            pass
        try:
            url += '&genre=%s' % quote_plus(i['genre'])
        except KeyError:
            try:
                url += '&genre=%s' % quote_plus(i['genre'].encode('utf-8'))
            except KeyError:
                pass
        except BaseException:
            pass
        try:
            url += '&dash=%s' % quote_plus(i['dash'])
        except BaseException:
            pass
        try:
            url += '&query=%s' % quote_plus(i['query'])
        except BaseException:
            pass

        cm = []
        menus = i['cm'] if 'cm' in i else []

        for menu in menus:
            try:
                try:
                    tmenu = control.lang(menu['title']).encode('utf-8')
                except BaseException:
                    tmenu = menu['title']
                qmenu = urlencode(menu['query'])
                cm.append((tmenu, 'RunPlugin(%s?%s)' % (sysaddon, qmenu)))
            except BaseException:
                pass

        meta = dict((k, v) for k, v in iteritems(i) if not k == 'cm' and not v == '0')

        if mediatype is not None:
            meta['mediatype'] = mediatype

        item = control.item(label=label, iconImage=image, thumbnailImage=image)

        item.setArt(
            {
                'icon': image, 'thumb': image, 'poster': image, 'tvshow.poster': image, 'season.poster': image,
                'banner': banner, 'tvshow.banner': banner, 'season.banner': banner, 'fanart': fanart
            }
        )

        item.addContextMenuItems(cm)
        item.setInfo(type=infotype, infoLabels=meta)

        if isFolder is False:
            if not i['action'] == 'pvr_client':
                item.setProperty('IsPlayable', 'true')
            else:
                item.setProperty('IsPlayable', 'false')
            if not i['action'] == 'pvr_client' and infotype == 'video':
                item.addStreamInfo('video', {'codec': 'h264'})

        control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder, totalItems=len(items))

    if content is not None:
        control.content(syshandle, content)

    control.directory(syshandle, cacheToDisc=cacheToDisc)


def resolve(url, meta=None, icon=None):

    item = control.item(path=url)

    if icon is not None:
        item.setArt({'icon': icon, 'thumb': icon})

    if meta is not None:
        item.setInfo(type='Video', infoLabels=meta)

    control.resolve(syshandle, True, item)


__all__ = ["add", "resolve"]
