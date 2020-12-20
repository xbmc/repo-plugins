# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
""" This is the actual VRT Radio audio plugin entry point """

from __future__ import absolute_import, division, unicode_literals

import routing
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItems, addSortMethod, endOfDirectory, setResolvedUrl, SORT_METHOD_LABEL, SORT_METHOD_UNSORTED

from data import CHANNELS

plugin = routing.Plugin()  # pylint: disable=invalid-name


@plugin.route('/')
def main_menu():
    """The VRT Radio plugin main menu"""
    radio_items = []
    for channel in CHANNELS:

        if channel.get('aac_128'):
            url = channel.get('aac_128')
        else:
            url = channel.get('mp3_128')

        item = ListItem(
            label=channel.get('label'),
            label2=channel.get('tagline'),
            path=url,
        )
        item.setArt(dict(icon=channel.get('logo'), fanart=channel.get('backdrop')))
        item.setInfo(type='video', infoLabels=dict(
            mediatype='music',
            plot='[B]%(label)s[/B]\n[I]%(tagline)s[/I]\n\n[COLOR yellow]%(website)s[/COLOR]' % channel,
        ))
        item.setProperty(key='IsPlayable', value='true')
        radio_items.append((url, item, False))

    ok = addDirectoryItems(plugin.handle, radio_items, len(radio_items))
    addSortMethod(plugin.handle, sortMethod=SORT_METHOD_UNSORTED)
    addSortMethod(plugin.handle, sortMethod=SORT_METHOD_LABEL)
    endOfDirectory(plugin.handle, ok)


@plugin.route('/play/<name>')
def play(name):
    channel = next((channel for channel in CHANNELS if channel['name'] == name), None)
    stream = channel.get('mp3_128')
    setResolvedUrl(plugin.handle, True, listitem=ListItem(path=stream))


@plugin.route('/iptv/channels')
def iptv_channels():
    """Return JSON-M3U formatted data for all live channels"""
    from iptvmanager import IPTVManager
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_channels()


@plugin.route('/iptv/epg')
def iptv_epg():
    """Return JSON-M3U formatted data for all live channels"""
    from iptvmanager import IPTVManager
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_epg()


def run(argv):
    ''' Addon entry point from wrapper '''
    plugin.run(argv)
