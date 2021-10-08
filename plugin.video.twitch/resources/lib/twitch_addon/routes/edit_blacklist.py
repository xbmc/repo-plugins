# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from six import PY2

from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Scripts
from ..addon.utils import i18n


def route(list_type='user', target_id=None, name=None, remove=False, refresh=False):
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
            if PY2 and isinstance(result[1], unicode):
                result[1] = result[1].encode('utf-8')
            kodi.notify(msg=i18n('removed_from_blacklist') % result[1], sound=False)

    if refresh:
        kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)
