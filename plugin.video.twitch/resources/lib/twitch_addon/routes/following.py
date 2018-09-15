# -*- coding: utf-8 -*-
from ..addon import menu_items
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n

from twitch.api.parameters import StreamType


def route():
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}})
    kodi.create_item({'label': i18n('playlists'), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.PLAYLIST},
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('playlists'))}})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('followed_channels'))
    context_menu.extend(menu_items.change_direction('followed_channels'))
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('clips'))
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.FOLLOWED, 'content': 'clips'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('clips'))}})
    kodi.end_of_directory(cache_to_disc=True)
