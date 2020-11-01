# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import socket
import struct
from contextlib import closing

from six.moves import xrange

from .logger import Logger

LOG = Logger()


def wake_servers(context):
    if context.settings.wake_on_lan():
        LOG.debug('Wake On LAN: true')
        servers = context.settings.get_wakeservers()
        for mac_address in servers:
            if mac_address:
                try:
                    LOG.debug('Waking server with MAC: %s' % mac_address)
                    wake_on_lan(mac_address)
                except ValueError:
                    LOG.debug('Incorrect MAC address format for server %s' % mac_address)
                except:  # pylint: disable=bare-except
                    LOG.debug('Unknown wake on lan error')


def wake_on_lan(mac_address):
    """ Switches on remote computers using WOL. """

    mac_address = mac_address.strip()

    # Check mac_address format and try to compensate.
    if len(mac_address) == 12:
        pass
    elif len(mac_address) == 12 + 5:
        mac_address = mac_address.replace(mac_address[2], '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', mac_address * 20])
    send_data = ''

    # Split up the hex values and pack.
    for i in xrange(0, len(data), 2):
        send_data = ''.join([send_data, struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as open_socket:
        open_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        open_socket.sendto(bytes(send_data), ('<broadcast>', 7))
