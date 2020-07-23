# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from six.moves.urllib_parse import urlparse

from ..constants import COMMANDS
from ..constants import CONFIG
from ..constants import MODES
from ..logger import Logger
from ..strings import i18n

LOG = Logger()


class ContextMenu:

    def __init__(self, context, server, url, data):
        self.context = context
        self.server = server
        self.data = data

        self.parsed_url = None
        if url:
            self.parsed_url = urlparse(url)

        self.item_id = self.data.get('ratingKey', '0')
        self.item_type = self.data.get('type', '').lower()

        self._context_menu = []
        self.create()

    @property
    def menu(self):
        return self._context_menu

    def create(self):
        if not self.parsed_url:
            return

        self._add_go_to_season()
        self._add_go_to_show()
        self._add_mark_watched()
        self._add_mark_unwatched()
        self._add_delete_from_playlist()
        self._add_add_to_playlist()
        self._add_delete_playlist()
        self._add_delete()
        self._add_audio()
        self._add_subtitles()
        self._add_update_library()
        self._add_refresh()

        LOG.debug('Using context menus:\n%s' % '\n'.join(map(str, self._context_menu)))

    def _add_go_to_season(self):
        if self.data.get('additional_context_menus', {}).get('go_to'):
            parent_id = self.data.get('parentRatingKey')
            if parent_id and self.data.get('season') is not None:
                self._context_menu.append(
                    (i18n('Go to') % (i18n('Season') + ' ' + str(self.data.get('season', 0))),
                     'Container.Update(plugin://%s/?mode=%s&url=%s&rating_key=%s)' %
                     (CONFIG['id'], MODES.TVEPISODES, self.server.get_uuid(), parent_id))
                )

    def _add_go_to_show(self):
        if self.data.get('additional_context_menus', {}).get('go_to'):
            grandparent_id = self.data.get('grandparentRatingKey')

            if grandparent_id and self.data.get('tvshowtitle') is not None:
                self._context_menu.append(
                    (i18n('Go to') % self.data.get('tvshowtitle'),
                     'Container.Update(plugin://%s/?mode=%s&url=%s&rating_key=%s)' %
                     (CONFIG['id'], MODES.TVSEASONS, self.server.get_uuid(), grandparent_id))
                )

    def _add_mark_watched(self):
        if self.item_type in ['video', 'season']:
            self._context_menu.append(
                (i18n('Mark as watched'),
                 'RunScript(' + CONFIG['id'] + ', %s, %s, %s, %s)' %
                 (COMMANDS.WATCH, self.server.get_uuid(), self.item_id, 'watch'))
            )

    def _add_mark_unwatched(self):
        if self.item_type in ['video', 'season']:
            self._context_menu.append(
                (i18n('Mark as unwatched'),
                 'RunScript(' + CONFIG['id'] + ', %s, %s, %s, %s)' %
                 (COMMANDS.WATCH, self.server.get_uuid(), self.item_id, 'unwatch'))
            )

    def _add_delete_from_playlist(self):
        if self.data.get('playlist_item_id'):
            playlist_title = self.data.get('playlist_title')
            playlist_url = self.data.get('playlist_url', self.parsed_url.path)
            self._context_menu.append(
                (i18n('Delete from playlist'),
                 'RunScript(' + CONFIG['id'] + ', %s, %s, %s, %s, %s, %s)'
                 % (COMMANDS.DELETEFROMPLAYLIST, self.server.get_uuid(), self.item_id,
                    playlist_title, self.data.get('playlist_item_id'), playlist_url))
            )

    def _add_add_to_playlist(self):
        if self.data.get('library_section_uuid'):
            playlist_type = ''
            if self.item_type == 'music':
                playlist_type = 'audio'
            elif self.item_type == 'video':
                playlist_type = 'video'
            elif self.item_type == 'image':
                playlist_type = 'photo'

            self._context_menu.append(
                (i18n('Add to playlist'),
                 'RunScript(' + CONFIG['id'] + ', %s, %s, %s, %s, %s)' %
                 (COMMANDS.ADDTOPLAYLIST, self.server.get_uuid(), self.item_id,
                  self.data.get('library_section_uuid'), playlist_type))
            )

    def _add_delete_playlist(self):
        if self.data.get('playlist') is True:
            self._context_menu.append(
                (i18n('Delete playlist'),
                 'RunScript(' + CONFIG['id'] + ', %s, %s, %s)' %
                 (COMMANDS.DELETEPLAYLIST, self.server.get_uuid(), self.item_id))
            )

    def _add_delete(self):
        if self.context.settings.show_delete_context_menu():
            self._context_menu.append(
                (i18n('Delete'), 'RunScript(' + CONFIG['id'] + ', %s, %s, %s)' %
                 (COMMANDS.DELETE, self.server.get_uuid(), self.item_id))
            )

    def _add_audio(self):
        item_source = self.data.get('source', '').lower()
        if self.item_type == 'video' and item_source in ['tvepisodes', 'movies']:
            self._context_menu.append(
                (i18n('Audio'), 'RunScript(' + CONFIG['id'] + ', %s, %s, %s)' %
                 (COMMANDS.AUDIO, self.server.get_uuid(), self.item_id))
            )

    def _add_subtitles(self):
        item_source = self.data.get('source', '').lower()
        if self.item_type == 'video' and item_source in ['tvepisodes', 'movies']:
            self._context_menu.append(
                (i18n('Subtitles'), 'RunScript(' + CONFIG['id'] + ', %s, %s, %s)' %
                 (COMMANDS.SUBS, self.server.get_uuid(), self.item_id))
            )

    def _add_update_library(self):
        try:
            section = self.parsed_url.path.split('/')[3]
            self._context_menu.append(
                (i18n('Update library'), 'RunScript(' + CONFIG['id'] + ', %s, %s, %s)' %
                 (COMMANDS.UPDATE, self.server.get_uuid(), section))
            )
        except IndexError:
            pass

    def _add_refresh(self):
        self._context_menu.append(
            (i18n('Refresh'),
             'RunScript(' + CONFIG['id'] + ', %s)' % COMMANDS.REFRESH)
        )
