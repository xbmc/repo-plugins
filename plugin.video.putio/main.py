# -*- coding: utf-8 -*-

# put.io kodi addon
# Copyright (C) 2009  Alper Kanat <alper@put.io>
# Copyright (C) 2016  Put.io Developers <devs@put.io>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import urlparse
import requests

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.helper import __lang__
from resources.lib.helper import __settings__
from resources.lib.helper import PutioApiHandler
from resources.lib.helper import PutioAuthFailureException

__url__ = sys.argv[0]  # base URL ('plugin://plugin.video.putio/')
__handle__ = int(sys.argv[1])  # process handle, as a numeric string
__args__ = urlparse.parse_qs(sys.argv[2].lstrip('?'))  # query string, ('?action=list&item=3')

PUTIO_KODI_ENDPOINT = 'https://put.io/xbmc'
RESOURCE_PATH = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media')


def build_url(action, item):
    return '{0}?action={1}&item={2}'.format(__url__, action, item)


def get_resource_path(filename):
    """Returns special path of the given filename."""
    if not filename:
        return
    return os.path.join(RESOURCE_PATH, filename)


def populate_dir(files):
    """Fills a directory listing with put.io files."""
    list_items = []
    for item in files:
        thumbnail = item.screenshot or get_resource_path('mid-folder.png')
        li = xbmcgui.ListItem(label=item.name,
                              label2=item.name,
                              iconImage=thumbnail,
                              thumbnailImage=thumbnail)

        # url when a delete action is triggered
        delete_ctx_url = build_url(action='delete', item=item.id)

        if item.is_folder:
            url = build_url(action='list', item=item.id)
        else:  # video or audio, no other types are available here
            url = build_url(action='play', item=item.id)

            # resumetime and totaltime are needed for Kodi to decide the file as watched or not.
            # FIXME: get total-time of the file and set to 'totaltime'
            li.setProperty(key='resumetime', value=str(item.start_from))
            li.setProperty(key='totaltime', value=str(20 * 60))

            # http://kodi.wiki/view/InfoLabels
            type_ = 'video' if item.is_video else 'music'
            li.setInfo(type=type_, infoLabels={'size': item.size, 'title': item.name})

        li.addContextMenuItems([
            (__lang__(32040), 'Container.Refresh'),  # refresh
            (__lang__(32042), 'XBMC.RunPlugin(%s)' % delete_ctx_url),  # delete
        ])
        list_items.append((url, li, item.is_folder))

    xbmcplugin.addDirectoryItems(handle=__handle__, items=list_items, totalItems=len(list_items))
    xbmcplugin.setContent(handle=__handle__, content='files')
    xbmcplugin.addSortMethod(handle=__handle__, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(handle=__handle__, sortMethod=xbmcplugin.SORT_METHOD_SIZE)
    xbmcplugin.endOfDirectory(handle=__handle__)


def play(item):
    """Plays the given item from where it was left off"""
    thumbnail = item.screenshot or item.icon

    li = xbmcgui.ListItem(label=item.name,
                          label2=item.name,
                          iconImage=thumbnail,
                          thumbnailImage=thumbnail)
    li.setInfo(type='video',
               infoLabels={
                   'size': item.size,
                   'title': item.name,
                   'mediatype': 'video',
               })
    # resume where it was left off
    li.setProperty(key='startoffset', value=str(item.start_from))
    li.setProperty(key='IsPlayable', value='true')

    li.setSubtitles([item.subtitles()])

    xbmc.Player().play(item=item.stream_url(), listitem=li)


def delete(item):
    """Deletes the given item and refreshes the current directory."""
    if item.id == 0:
        return

    response = xbmcgui.Dialog().yesno(heading=__lang__(32060), line1=__lang__(32061))

    # yes=1, no=0
    if response == 0:
        return

    item.delete()
    xbmc.executebuiltin('Container.Refresh')


def main():
    """Dispatches the commands."""

    handler = PutioApiHandler(__settings__.getSetting('oauth2_token'))
    item_id = __args__.get('item')
    if not item_id:
        populate_dir(handler.list(parent=0))
        return

    item_id = item_id[0]
    item = handler.get(id_=item_id)
    if not item.content_type:
        return

    # Dispatch commands
    action = __args__.get('action')
    if not action:
        return

    action = action[0]
    if action == 'list':
        populate_dir(handler.list(parent=item_id))
        return

    if action == 'delete':
        delete(item=item)
        return

    if action == 'play':
        play(item=item)
        return


if __name__ == '__main__':
    try:
        main()
    except PutioAuthFailureException as e:
        # FIXME: request might fail
        r = requests.get(PUTIO_KODI_ENDPOINT + '/getuniqueid')
        # FIXME: json parsing might fail
        uniqueid = r.json()['id']

        xbmcgui.Dialog().ok(heading=__lang__(32022),
                            line1=__lang__(32023) % uniqueid,
                            line2=__lang__(32024))

        try:
            # request oauth2 token in exchange to this unique id.
            r = requests.get(PUTIO_KODI_ENDPOINT + '/k/%s' % uniqueid)
            oauth2_token = r.json()['oauthtoken']
            if oauth2_token:
                __settings__.setSetting('oauth2_token', str(oauth2_token))
                main()
        except Exception as e:
            xbmc.log(msg='Error while fetching oauth2 token. error: %s' % e, level=xbmc.LOGERROR)
            xbmcgui.Dialog().ok(header=__lang__(32020), header1=str(e))
