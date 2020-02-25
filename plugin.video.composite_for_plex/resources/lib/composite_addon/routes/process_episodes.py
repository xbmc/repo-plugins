# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..addon.processing.episodes import process_episodes
from ..plex import plex


def run(context, url, rating_key=None, library=False):
    context.plex_network = plex.Plex(context.settings, load=True)
    process_episodes(context, url, rating_key=rating_key, library=library)
