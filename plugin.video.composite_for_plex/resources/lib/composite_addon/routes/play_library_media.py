# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..addon.data_cache import DATA_CACHE
from ..addon.playback import play_library_media
from ..addon.playback import play_media_id_from_uuid
from ..addon.utils import get_transcode_profile
from ..plex import plex


def run(context, data):
    context.plex_network = plex.Plex(context.settings, load=True)

    if data['transcode'] and data['transcode_profile'] is None:
        data['transcode_profile'] = get_transcode_profile(context)
    if data['transcode_profile'] is None:
        data['transcode_profile'] = 0

    if data['url'] is None and (data['server_uuid'] and data['media_id']):
        play_media_id_from_uuid(context, data)
        DATA_CACHE.delete_cache(True)
        return

    if data['url']:
        play_library_media(context, data)
        DATA_CACHE.delete_cache(True)
