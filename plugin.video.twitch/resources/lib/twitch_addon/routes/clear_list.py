# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.common import kodi
from ..addon.utils import i18n


def route(list_type, list_name):
    confirmed = kodi.Dialog().yesno(i18n('clear_list'), i18n('confirm_clear') % (list_type, list_name))
    if confirmed:
        result = utils.clear_list(list_type, list_name)
        if result:
            kodi.notify(msg=i18n('cleared_list') % (list_type, list_name), sound=False)
