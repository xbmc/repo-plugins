# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..plex import plex
from ..plex import plexsignin

LOG = Logger()


def run(context):
    context.plex_network = plex.Plex(context.settings, load=False)
    _ = plexsignin.switch_user(context)
    context.plex_network.delete_cache()
    DATA_CACHE.delete_cache(True)
