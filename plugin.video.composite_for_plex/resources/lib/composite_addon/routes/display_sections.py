# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..addon.common import get_handle
from ..addon.constants import COMMANDS
from ..addon.constants import CONFIG
from ..addon.constants import MODES
from ..addon.containers import GUIItem
from ..addon.items.gui import create_gui_item
from ..addon.logger import Logger
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context, content_filter=None, display_shared=False):
    context.plex_network = plex.Plex(context.settings, load=True)
    xbmcplugin.setContent(get_handle(), 'files')

    server_list = context.plex_network.get_server_list()
    LOG.debug('Using list of %s servers: %s' % (len(server_list), server_list))

    items = []
    append_item = items.append

    menus = context.settings.show_menus()

    server_section_menus, playlist_section_menus = \
        server_section_menus_items(context, server_list, content_filter, display_shared, menus)

    if server_section_menus:
        items += combined_sections_item(context)

    items += server_section_menus

    if display_shared:
        if items:
            xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

        xbmcplugin.endOfDirectory(get_handle(),
                                  cacheToDisc=context.settings.cache_directory())
        return

    if menus.get('playlists') and context.plex_network.is_myplex_signedin():
        items += playlist_section_menus

    if menus.get('composite_playlist') and context.plex_network.is_myplex_signedin():
        items += composite_playlist_item(context)

    # For each of the servers we have identified
    if menus.get('queue') and context.plex_network.is_myplex_signedin():
        details = {
            'title': i18n('myPlex Queue')
        }
        extra_data = {
            'type': 'Folder',
            'mode': MODES.MYPLEXQUEUE
        }
        gui_item = GUIItem('http://myplexqueue', details, extra_data)
        append_item(create_gui_item(context, gui_item))

    items += server_additional_menu_items(context, server_list, content_filter, menus)
    items += action_menu_items(context)

    if items:
        xbmcplugin.addDirectoryItems(get_handle(), items, len(items))

    xbmcplugin.endOfDirectory(get_handle(), cacheToDisc=context.settings.cache_directory())


def composite_playlist_item(context):
    details = {
        'title': i18n('Composite Playlist')
    }
    extra_data = {
        'type': 'file'
    }

    item_url = 'cmd:' + COMMANDS.COMPOSITE_PLAYLIST
    gui_item = GUIItem(item_url, details, extra_data)
    return [create_gui_item(context, gui_item)]


def combined_sections_item(context):
    details = {
        'title': i18n('Combined Sections')
    }
    extra_data = {
        'type': 'Folder',
        'mode': MODES.COMBINED_SECTIONS
    }
    gui_item = GUIItem('http://combined_sections', details, extra_data)
    return [create_gui_item(context, gui_item)]


def server_section_menus_items(context, server_list, content_filter, display_shared, menus):
    settings = {
        'picture_mode': context.settings.get_picture_mode(),
        'prefix_server': context.settings.prefix_server(),
        'use_context_menus': not context.settings.skip_context_menus(),
    }

    items = []
    playlist_items = []
    for server in server_list:

        sections = server.get_sections()
        url_location = server.get_url_location()
        server_uuid = server.get_uuid()
        server_name = server.get_name()

        prefix_server = context.settings.prefix_server()
        if not prefix_server or (prefix_server and len(server_list) > 1):
            prefix = server.get_name() + ': '
        else:
            prefix = ''

        server_items = []
        for section in sections:

            if (display_shared and server.is_owned() or
                    (content_filter is not None and section.content_type() != content_filter)):
                continue

            if section.content_type() is None:
                LOG.debug('Ignoring section %s: %s of type %s as unable to process'
                          % (server_name, section.get_title(), section.get_type()))
                continue

            if not settings.get('picture_mode') and section.is_photo():
                # photos only work from the picture add-ons
                continue

            details = {
                'title': prefix + section.get_title()
            }

            extra_data = {
                'fanart_image': server.get_fanart(section),
                'type': 'Folder'
            }

            path = section.get_path()

            if context.settings.secondary_menus():
                mode = MODES.GETCONTENT
            else:
                mode = section.mode()
                path = path + '/all'

            extra_data['mode'] = mode
            section_url = server.join_url(url_location, path)
            context_menu = None
            if settings.get('use_context_menus'):
                context_menu = [(i18n('Refresh library section'),
                                 'RunScript(' + CONFIG['id'] + ', update, %s, %s)' %
                                 (server_uuid, section.get_key()))]

            # Build that listing..
            gui_item = GUIItem(section_url, details, extra_data, context_menu)
            server_items.append(create_gui_item(context, gui_item))

        if server_items:
            if menus.get('playlists'):
                # create playlist link
                details = {
                    'title': prefix + i18n('Playlists')
                }
                extra_data = {
                    'type': 'Folder',
                    'mode': MODES.PLAYLISTS
                }
                item_url = server.join_url(url_location, 'playlists')
                gui_item = GUIItem(item_url, details, extra_data)
                playlist_items.append(create_gui_item(context, gui_item))

            items += server_items

    return items, playlist_items


def server_additional_menu_items(context, server_list, content_filter, menus):
    prefix_server = context.settings.prefix_server()

    items = []
    append_item = items.append
    for server in server_list:

        if server.is_offline() or server.is_secondary():
            continue

        # Plex plugin handling
        if (content_filter is not None) and (content_filter != 'plugins'):
            continue

        if not prefix_server or (prefix_server and len(server_list) > 1):
            prefix = server.get_name() + ': '
        else:
            prefix = ''

        if menus.get('channels'):
            details = {
                'title': prefix + i18n('Channels')
            }
            extra_data = {
                'type': 'Folder',
                'mode': MODES.CHANNELVIEW
            }

            item_url = server.join_url(server.get_url_location(), 'channels/all')
            gui_item = GUIItem(item_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

        if menus.get('online'):
            # Create plexonline link
            details = {
                'title': prefix + i18n('Plex Online')
            }
            extra_data = {
                'type': 'Folder',
                'mode': MODES.PLEXONLINE
            }
            item_url = server.join_url(server.get_url_location(), 'system/plexonline')
            gui_item = GUIItem(item_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

        if menus.get('widgets'):
            # create Widgets link
            details = {
                'title': prefix + i18n('Widgets')
            }
            extra_data = {
                'type': 'Folder',
                'mode': MODES.WIDGETS
            }

            item_url = server.get_url_location()
            gui_item = GUIItem(item_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

    return items


def action_menu_items(context):
    items = []
    append_item = items.append
    if context.plex_network.is_myplex_signedin():

        if context.plex_network.is_plexhome_enabled():
            details = {
                'title': i18n('Switch User')
            }
            extra_data = {
                'type': 'file'
            }

            item_url = 'cmd:' + COMMANDS.SWITCHUSER
            gui_item = GUIItem(item_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))

        details = {
            'title': i18n('Sign Out')
        }
        extra_data = {
            'type': 'file'
        }

        item_url = 'cmd:' + COMMANDS.SIGNOUT
        gui_item = GUIItem(item_url, details, extra_data)
        append_item(create_gui_item(context, gui_item))

        details = {
            'title': i18n('Detect Servers')
        }
        extra_data = {
            'type': 'file'
        }
        item_url = 'cmd:' + COMMANDS.DETECTSERVERS
        gui_item = GUIItem(item_url, details, extra_data)
        append_item(create_gui_item(context, gui_item))

        details = {
            'title': i18n('Manage Servers')
        }
        extra_data = {
            'type': 'file'
        }
        item_url = 'cmd:' + COMMANDS.MANAGESERVERS
        gui_item = GUIItem(item_url, details, extra_data)
        append_item(create_gui_item(context, gui_item))

        if context.settings.cache():
            details = {
                'title': i18n('Clear Caches')
            }
            extra_data = {
                'type': 'file'
            }
            item_url = 'cmd:' + COMMANDS.DELETEREFRESH
            gui_item = GUIItem(item_url, details, extra_data)
            append_item(create_gui_item(context, gui_item))
    else:
        details = {
            'title': i18n('Sign In')
        }
        extra_data = {
            'type': 'file'
        }

        item_url = 'cmd:' + COMMANDS.SIGNIN
        gui_item = GUIItem(item_url, details, extra_data)
        append_item(create_gui_item(context, gui_item))

    return items
