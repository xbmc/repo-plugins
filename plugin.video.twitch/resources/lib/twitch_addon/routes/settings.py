# -*- coding: utf-8 -*-
from ..addon.common import kodi
from ..addon.constants import Scripts


def route(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)
