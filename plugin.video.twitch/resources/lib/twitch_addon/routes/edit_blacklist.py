# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.common import kodi
from ..addon.utils import i18n


def route(list_type='user', target_id=None, name=None, remove=False):
    if not remove:
        if not target_id or not name: return
        if kodi.get_setting('blacklist_confirm_toggle') == 'true':
            confirmed = kodi.Dialog().yesno(i18n('blacklist'), i18n('confirm_blacklist') % name)
            if confirmed:
                result = utils.add_blacklist(target_id, name, list_type)
                if result:
                    kodi.notify(msg=i18n('blacklisted') % name, sound=False)
        else:
            result = utils.add_blacklist(target_id, name, list_type)
    else:
        result = utils.remove_blacklist(list_type)
        if result:
            kodi.notify(msg=i18n('removed_from_blacklist') % result[1], sound=False)
