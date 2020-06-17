# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT Radio audio plugin entry point '''

from __future__ import absolute_import, division, unicode_literals
import routing
from data import CHANNELS

from xbmc import getCondVisibility
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItems, addSortMethod, endOfDirectory, setResolvedUrl, SORT_METHOD_LABEL, SORT_METHOD_UNSORTED

plugin = routing.Plugin()  # pylint: disable=invalid-name


@plugin.route('/')
def main_menu(path=''):
    """The VRT Radio plugin main menu"""

    has_white_icons = getCondVisibility('System.HasAddon("resource.images.studios.white")') == 1
    if has_white_icons:
        icon_path = 'resource://resource.images.studios.white/%(studio)s.png'
        thumb_path = 'resource://resource.images.studios.white/%(studio)s.png'
    else:
        icon_path = 'DefaultAddonMusic.png'
        thumb_path = 'DefaultAddonMusic.png'

    # NOTE: Wait for resource.images.studios.coloured v0.16 to be released
    # has_coloured_icons = getCondVisibility('System.HasAddon("resource.images.studios.coloured")') == 1
    # if has_coloured_icons:
    #     thumb_path = 'resource://resource.images.studios.coloured/%(studio)s.png'

    radio_items = []
    for channel in CHANNELS:
        icon = icon_path % channel
        thumb = thumb_path % channel
        # url = plugin.url_for(play, name=channel.get('name'))
        url = channel.get('aac_128')

        item = ListItem(
            label=channel.get('label'),
            label2=channel.get('tagline'),
            iconImage=icon,
            thumbnailImage=thumb,
            path=url,
        )
        item.setArt(dict(thumb=channel.get('logo'), icon=icon, fanart=icon))
        item.setInfo(type='video', infoLabels=dict(
            mediatype='music',
            plot='[B]%(label)s[/B]\n[I]%(tagline)s[/I]\n\n[COLOR yellow]%(website)s[/COLOR]' % channel,
        ))
        item.setProperty(key='IsPlayable', value='true')
        item.setProperty(key='fanart_image', value=icon)
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
