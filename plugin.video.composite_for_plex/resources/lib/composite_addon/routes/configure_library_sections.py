# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error

from ..addon.constants import CONFIG
from ..addon.library_sections import LibrarySectionsStore
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context, reset=False):
    context.plex_network = plex.Plex(context.settings, load=True)
    section_storage = LibrarySectionsStore()

    if reset:
        reset_selection(section_storage)
        return

    dialog = xbmcgui.Dialog()
    use_details = CONFIG['kodi_version'] > 16

    all_sections = context.plex_network.all_sections()

    LOG.debug('Using list of %s sections: %s' % (len(all_sections), all_sections))

    movie_sections, tvshow_sections = get_sections(context, all_sections, use_details)

    preselect, select_from = selected_section_info(section_storage, 'movie',
                                                   movie_sections, use_details)
    selected_movie_sections = dialog.multiselect(i18n('Library - Movie Sections'), select_from,
                                                 preselect=preselect, useDetails=use_details)
    update_sections(section_storage, 'movie', movie_sections, selected_movie_sections)

    preselect, select_from = selected_section_info(section_storage, 'show',
                                                   tvshow_sections, use_details)
    selected_tvshow_sections = dialog.multiselect(i18n('Library - TV Show Sections'), select_from,
                                                  preselect=preselect, useDetails=use_details)
    update_sections(section_storage, 'show', tvshow_sections, selected_tvshow_sections)


def reset_selection(storage):
    storage.reset_to_default()
    xbmcgui.Dialog().notification(CONFIG['name'],
                                  i18n('Configured library sections have been reset'),
                                  icon=CONFIG['icon'], time=5000, sound=False)


def update_sections(storage, section_type, sections, selected_sections):
    if isinstance(selected_sections, list):
        if section_type == 'movie':
            storage.remove_all_movie_sections()
        elif section_type == 'show':
            storage.remove_all_tvshow_sections()

        for selection in selected_sections:
            selected = sections[selection]

            if section_type == 'movie':
                storage.add_movie_section(selected[1], selected[2])
            elif section_type == 'show':
                storage.add_tvshow_section(selected[1], selected[2])


def get_sections(context, sections, details):
    movie_sections = []
    tvshow_sections = []

    for section in sections:
        if not section.is_show() and not section.is_movie():
            continue

        section_uuid = section.get_uuid()

        server_uuid = section.get_server_uuid()
        try:
            server = context.plex_network.get_server_from_uuid(server_uuid)
        except KeyError:
            LOG.debug('Failed to map server from uuid.\nSection UUID: %s\n'
                      'Section: %s\nServer UUID: %s' %
                      (section_uuid, section, server_uuid))
            continue

        server_name = server.get_name()

        list_item = None
        section_title = section.get_title()
        if details:
            if CONFIG['kodi_version'] > 17:
                list_item = xbmcgui.ListItem(offscreen=True)
            else:
                list_item = xbmcgui.ListItem()

            list_item.setArt({
                'icon': CONFIG['icon'],
                'thumb': CONFIG['icon']
            })
            list_item.setLabel(section_title)
            list_item.setLabel2(server_name)

        else:
            section_title = '%s: %s' % (server_name, section_title)

        if section.is_movie():
            movie_sections.append((server, server_uuid, section_uuid, section_title, list_item))

        elif section.is_show():
            tvshow_sections.append((server, server_uuid, section_uuid, section_title, list_item))

    return movie_sections, tvshow_sections


def selected_section_info(storage, section_type, sections, details):
    preselect = []
    select_from = []

    for index, section in enumerate(sections):
        stored_sections = []
        if section_type == 'movie':
            stored_sections = storage.get_sections(section[1]).get('movie')
        elif section_type == 'show':
            stored_sections = storage.get_sections(section[1]).get('show')

        if stored_sections and section[2] in stored_sections:
            preselect.append(index)

        if details:
            select_from.append(section[4])
        else:
            select_from.append(section[3])

    return preselect, select_from
