# -*- coding: utf-8 -*-
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n


def route(content):
    if MODES.SEARCHRESULTS not in kodi.get_info_label('Container.FolderPath'):
        kodi.set_view('files', set_sort=False)
        user_input = kodi.get_keyboard(i18n('search'))
        if user_input:
            kodi.end_of_directory()
            kodi.update_container(kodi.get_plugin_url({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': user_input, 'index': 0}))
        else:
            return
    else:
        return
