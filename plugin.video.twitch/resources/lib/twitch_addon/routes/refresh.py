# -*- coding: utf-8 -*-
from ..addon.common import kodi
from ..addon.constants import Scripts


def route():
    kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)

