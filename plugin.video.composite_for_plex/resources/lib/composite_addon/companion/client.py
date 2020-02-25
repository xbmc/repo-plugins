# -*- coding: utf-8 -*-
"""

    Copyright (C) 2013-2019 PleXBMC Helper (script.plexbmc.helper)
        by wickning1 (aka Nick Wing), hippojay (Dave Hawes-Johnson)
    Copyright (C) 2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..addon.constants import CONFIG
from ..addon.logger import Logger
from ..plex.plexgdm import PlexGDM

LOG = Logger()


# Start GDM for server/client discovery
def get_client(settings):
    client = PlexGDM()
    details = settings.companion_receiver()
    data = {
        'uuid': details['uuid'],
        'name': details['name'],
        'port': details['port'],
        'product': {
            'name': CONFIG['name'],
            'version': CONFIG['version'],
        }
    }
    client.client_details(data)

    LOG.debug('Registration string is: %s' % client.get_client_details())
    return client
