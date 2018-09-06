# -*- coding: utf-8 -*-
from ..addon.common import kodi
from ..addon.constants import REFRESH_SCRIPT


def route():
    kodi.execute_builtin('RunScript(%s)' % REFRESH_SCRIPT)

