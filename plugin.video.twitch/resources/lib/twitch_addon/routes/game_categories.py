# -*- coding: utf-8 -*-
from ..addon import menu_items
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n


def route(game):
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    context_menu.extend(menu_items.clear_previews())
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.GAMESTREAMS, 'game': game}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (game, i18n('live_channels'))}})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'game': game},
                      'info': {'plot': '%s - %s' % (game, i18n('videos'))}})
    kodi.end_of_directory()
