# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
import logging
import routing

from helpers.helperclasses import EPG
from yelo_exceptions import YeloException
from yelo import Yelo

logging.basicConfig()
_LOGGER = logging.getLogger('plugin')
plugin = routing.Plugin()  # pylint: disable=invalid-name

# instantiate yelo object
yelo = Yelo()  # pylint: disable=invalid-name


@plugin.route('/')
def main_menu():
    if EPG().is_enabled and EPG().is_cached:
        yelo.list_channels()
    else:
        yelo.list_channels_without_epg()


@plugin.route('/play/id/<channel_id>')
def play_id(channel_id):
    try:
        yelo.play(channel_id)
    except YeloException as exc:
        _LOGGER.error(exc)


@plugin.route('/iptv/channels')
def iptv_channels():
    from iptvmanager import IPTVManager
    port = int(plugin.args['port'][0])
    IPTVManager(port, yelo).send_channels()


@plugin.route('/iptv/epg')
def iptv_epg():
    from iptvmanager import IPTVManager
    port = int(plugin.args['port'][0])
    IPTVManager(port, yelo).send_epg()


def run(argv):
    plugin.run(argv)


@plugin.route('/epg/refresh')
def epg_refresh():
    from yelo_bg_service import refresh_epg
    refresh_epg()
