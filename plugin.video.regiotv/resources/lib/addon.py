# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' This is the actual Regio TV video plugin entry point '''

from __future__ import absolute_import, division, unicode_literals
from routing import Plugin
from data import CHANNELS

plugin = Plugin()  # pylint: disable=invalid-name


@plugin.route('/')
def main_menu():
    ''' The Regio TV plugin main menu '''
    from xbmcaddon import Addon
    from xbmcgui import ListItem
    import xbmcplugin

    xbmcplugin.setContent(plugin.handle, content='files')
    xbmcplugin.setPluginCategory(plugin.handle, category='Zenders')
    xbmcplugin.setPluginFanart(plugin.handle, image=Addon().getAddonInfo('fanart'))
    xbmcplugin.addSortMethod(plugin.handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(plugin.handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)

    listing = []
    for channel in CHANNELS:
        is_folder = False
        is_playable = True

        label = '{name} [COLOR gray]| {label}[/COLOR]'.format(**channel)
        plot = '[B]{name}[/B]\nRegio {label}\n\n[I]{description}[/I]\n\n[COLOR yellow]{website}[/COLOR]'.format(**channel)
        list_item = ListItem(label=label, label2=channel.get('label'), offscreen=True)
        list_item.setProperty(key='IsPlayable', value='true' if is_playable else 'false')
        list_item.setInfo(type='video', infoLabels=dict(
            lastplayed='',
            mediatype='video',
            playcount=0,
            plot=plot,
        ))
        list_item.setArt(dict(
            icon='DefaultAddonPVRClient.png',
            thumb=channel.get('logo'),
        ))

        # FIXME: The setIsFolder method is new in Kodi18, so we cannot use it just yet.
        # list_item.setIsFolder(is_folder)

        url = channel.get('live_stream')
        if channel.get('referer'):
            url += '|referer=' + channel.get('referer')
        listing.append((url, list_item, is_folder))

    succeeded = xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    xbmcplugin.endOfDirectory(plugin.handle, succeeded, updateListing=False, cacheToDisc=True)


@plugin.route('/iptv/channels')
def iptv_channels():
    """Return JSON-M3U formatted data for all live channels"""
    from iptvmanager import IPTVManager
    port = int(plugin.args.get('port')[0])
    IPTVManager(port).send_channels()


def run(argv):
    ''' Addon entry point from wrapper '''
    plugin.run(argv)
