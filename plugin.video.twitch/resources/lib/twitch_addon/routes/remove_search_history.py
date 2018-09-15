# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import REFRESH_SCRIPT
from ..addon.utils import i18n


def route(search_type, query, refresh=True):
    query_label = '\'[B]%s[/B]\'' % query
    confirmed = kodi.Dialog().yesno(i18n('confirm'), i18n('remove_from_search_history_') % query_label)
    if confirmed:
        history = utils.get_search_history(search_type)
        if history:
            history.remove(query)
            kodi.notify(msg=i18n('removed_from_search_history') % query_label, sound=False)
            if refresh:
                kodi.execute_builtin('RunScript(%s)' % REFRESH_SCRIPT)
