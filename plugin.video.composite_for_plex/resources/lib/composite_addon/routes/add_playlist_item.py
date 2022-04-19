# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from six import PY3

from ..addon.common import get_argv
from ..addon.constants import CONFIG
from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()
DIALOG = xbmcgui.Dialog()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=True)
    server_uuid = get_argv()[2]
    metadata_id = get_argv()[3]
    library_section_uuid = get_argv()[4]
    playlist_type = get_argv()[5]

    server = context.plex_network.get_server_from_uuid(server_uuid)

    selected = playlist_user_select(server)
    if selected is None:
        return

    LOG.debug('choosing playlist: %s' % selected)

    playlist_title = ''
    item = server.get_metadata(metadata_id)[0]
    item_title = item.get('title', '')
    if selected.get('key') == 'CREATEAPLAYLIST':
        playlist_title = get_playlist_title(item_title)
        if not playlist_title:
            return

    item_image = server.get_kodi_header_formatted_url(
        server.join_url(server.get_url_location(), item.get('thumb'))
    )
    if playlist_type and playlist_title:
        selected['title'] = playlist_title
        response = server.create_playlist(metadata_id, playlist_title, playlist_type)
    else:
        response = server.add_playlist_item(selected.get('key'), library_section_uuid, metadata_id)
    if response and not response.get('status'):
        if playlist_type and playlist_title:
            success = response.get('size') == '1'
        else:
            leaf_added = int(response.get('leafCountAdded', 0))
            leaf_requested = int(response.get('leafCountRequested', 0))
            success = leaf_added > 0 and leaf_added == leaf_requested

        if success:
            DIALOG.notification(CONFIG['name'], i18n('Added to the playlist') %
                                (item_title, selected.get('title')), item_image)
            DATA_CACHE.delete_cache(True)
            return

        DIALOG.notification(CONFIG['name'], i18n('is already in the playlist') %
                            (item_title, selected.get('title')), item_image)
        return

    DIALOG.notification(CONFIG['name'], i18n('Failed to add to the playlist') %
                        (item_title, selected.get('title')), item_image)


def playlist_user_select(server):
    playlists = [{
        'title': i18n('Create a playlist'),
        'key': 'CREATEAPLAYLIST',
        'image': CONFIG['icon'],
        'summary': '',
    }]
    append_playlist = playlists.append
    get_formatted_url = server.get_formatted_url
    tree = server.get_playlists()

    if PY3:
        playlist_iter = tree.iter('Playlist')
    else:
        playlist_iter = tree.getiterator('Playlist')

    for playlist in playlist_iter:
        image = ''
        if playlist.get('composite'):
            image = get_formatted_url(server.join_url(server.get_url_location(),
                                                      playlist.get('composite')))
        append_playlist({
            'title': playlist.get('title'),
            'key': playlist.get('ratingKey'),
            'image': image,
            'summary': playlist.get('summary'),
        })

    if CONFIG['kodi_version'] > 16:
        item_constructor = xbmcgui.ListItem
        select_items = []
        append_item = select_items.append

        for playlist in playlists:
            list_item = item_constructor(label=playlist.get('title'),
                                         label2=playlist.get('summary'))
            list_item.setArt({
                'icon': playlist.get('image'),
                'thumb': playlist.get('image'),
                'poster': playlist.get('image'),
            })
            append_item(list_item)

        return_value = DIALOG.select(i18n('Select playlist'), select_items,
                                     useDetails=True)
    else:
        select_items = list(map(lambda x: x.get('title'), playlists))
        return_value = DIALOG.select(i18n('Select playlist'), select_items)

    if return_value == -1:
        LOG.debug('Dialog cancelled')
        return None

    return playlists[return_value]


def get_playlist_title(line):
    keyboard = xbmc.Keyboard(line, i18n('Enter a playlist title'))
    keyboard.doModal()
    if keyboard.isConfirmed():
        playlist_title = keyboard.getText()
        playlist_title = playlist_title.strip()
        return playlist_title
    return ''
