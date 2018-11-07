# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Scripts
from ..addon.utils import i18n


def route(search_type, refresh=False):
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('clear_search_history_'))
    if confirmed:
        history = utils.get_search_history(search_type)
        if history:
            history.clear()
            kodi.notify(msg=i18n('search_history_cleared'), sound=False)
            if refresh:
                kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)
