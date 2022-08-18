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
from urllib.parse import parse_qs
import requests

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.helper import I18N
from resources.lib.helper import SETTINGS
from resources.lib.helper import PutioApiHandler
from resources.lib.helper import PutioAuthFailureException

PLUGIN_URL = sys.argv[0]  # base URL ('plugin://plugin.video.putio/')
PLUGIN_HANDLE = int(sys.argv[1])  # process handle, as a numeric string
PLUGIN_ARGS = parse_qs(sys.argv[2].lstrip('?'))  # query string, ('?action=list&item=3')

PUTIO_KODI_ENDPOINT = 'https://put.io/kodi'
RESOURCE_PATH = os.path.join(SETTINGS.getAddonInfo('path'), 'resources', 'media')


def build_url(action, item):
    return '{0}?action={1}&item={2}'.format(PLUGIN_URL, action, item)


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
                              label2=item.name)
        li.setArt({
            'icon': thumbnail,
            'thumb': thumbnail
        })

        # If known prehand, this can (but does not have to) avoid HEAD requests being sent to HTTP servers to figure out
        # file type.
        # http://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem-setMimeType
        li.setMimeType(mimetype=item.content_type)

        # http://kodi.wiki/view/InfoLabels
        info_labels = {
            'date': item.created_at.strftime('%d.%m.%Y'),
            'size': item.size,
            'title': item.name,
        }

        if item.is_video:
            item_type = 'video'
            url = build_url(action='play', item=item.id)
            li.setProperty(key='IsPlayable', value='true')

            info_labels['mediatype'] = 'video'

            if hasattr(item, 'video_metadata') and item.video_metadata:
                metadata = item.video_metadata

                duration = metadata['duration']
                video_offset = item.start_from if hasattr(item, 'start_from') else 0

                # mark the video as watched if there is 5% progress left
                video_finished = duration and ((duration - video_offset) <= (duration * 0.05))

                if duration:
                    info_labels['duration'] = duration
                    if video_finished:
                        info_labels['playcount'] = str(1)

                # resumetime and totaltime are the undocumented properties to show resumable icon.
                if (not video_finished) and video_offset:
                    li.setProperty(key='resumetime', value=str(video_offset))
                if duration:
                    li.setProperty(key='totaltime', value=str(duration))

        elif item.is_folder:
            # folder's type can be 'video' if you are passing it to setInfo method. Kodi authors said this. So, who
            # cares.
            item_type = 'video'
            url = build_url(action='list', item=item.id)
        elif item.is_audio:
            item_type = 'music'
            url = build_url(action='play', item=item.id)
            li.setProperty(key='IsPlayable', value='true')
        else:  # video or audio, no other types are available here
            continue

        li.setInfo(type=item_type, infoLabels=info_labels)

        context_menu_items = [(I18N(32040), 'Container.Refresh')]
        if not item.is_shared:
            # url when a delete action is triggered
            delete_ctx_url = build_url(action='delete', item=item.id)
            context_menu_items.append(
                (I18N(32042), 'RunPlugin(%s)' % delete_ctx_url))  # delete context

        li.addContextMenuItems(context_menu_items)
        list_items.append((url, li, item.is_folder))

    xbmcplugin.addDirectoryItems(handle=PLUGIN_HANDLE, items=list_items, totalItems=len(list_items))
    xbmcplugin.setContent(handle=PLUGIN_HANDLE, content='files')

    xbmcplugin.addSortMethod(handle=PLUGIN_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    xbmcplugin.addSortMethod(handle=PLUGIN_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(handle=PLUGIN_HANDLE, sortMethod=xbmcplugin.SORT_METHOD_SIZE)

    xbmcplugin.endOfDirectory(handle=PLUGIN_HANDLE)


def play(item):
    """Plays the given item from where it was left off"""

    thumbnail = item.screenshot or item.icon
    li = xbmcgui.ListItem(label=item.name,
                          label2=item.name)
    li.setArt({
        'icon': thumbnail,
        'thumb': thumbnail
    })

    li.setInfo(type='video',
               infoLabels={
                   'size': item.size,
                   'title': item.name,
                   'mediatype': 'video',
               })

    li.setPath(item.stream_url())
    li.setSubtitles(item.subtitles())

    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, succeeded=True, listitem=li)


def delete(item):
    """Deletes the given item and refreshes the current directory."""
    if item.id == 0:
        return

    response = xbmcgui.Dialog().yesno(heading=I18N(32060), message=I18N(32061))

    # yes=1, no=0
    if response == 0:
        return

    item.delete()
    xbmc.executebuiltin('Container.Refresh')


def main():
    """Dispatches the commands."""

    handler = PutioApiHandler(SETTINGS.getSetting('oauth2_token'))
    item_id = PLUGIN_ARGS.get('item')
    if not item_id:  # Entrypoint.
        # if the user has an account but no product,
        # she could walk the files but couldn't play them. Inform.
        if not handler.is_account_active():
            xbmcgui.Dialog().ok(heading=I18N(32062), message=I18N(32063))

        populate_dir(handler.list(parent=0))
        return

    item_id = int(item_id[0])
    item = handler.get(id_=item_id)
    if not item.content_type:
        return

    # Dispatch commands
    action = PLUGIN_ARGS.get('action')
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

        xbmcgui.Dialog().ok(heading=I18N(32022), message='{msg1}\n{msg2}'.format(msg1 = I18N(32023) % uniqueid, msg2=I18N(32024)))

        try:
            # request oauth2 token in exchange to this unique id.
            r = requests.get(PUTIO_KODI_ENDPOINT + '/k/%s' % uniqueid)
            oauth2_token = r.json()['oauthtoken']
            if oauth2_token:
                SETTINGS.setSetting('oauth2_token', str(oauth2_token))
                main()
        except Exception as e:
            xbmc.log(msg='Error while fetching oauth2 token. error: %s' % e, level=xbmc.LOGERROR)
            xbmcgui.Dialog().ok(heading='{heading}\n{error}'.format(heading=I18N(32020), error=str(e)))
