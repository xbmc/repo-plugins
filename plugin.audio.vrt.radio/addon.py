# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' This is the actual VRT Radio audio plugin entry point '''

from __future__ import absolute_import, division, unicode_literals

from channels import CHANNELS
import routing
from xbmc import getCondVisibility
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItems, addSortMethod, endOfDirectory, setResolvedUrl, SORT_METHOD_LABEL, SORT_METHOD_UNSORTED

plugin = routing.Plugin()


@plugin.route('/')
def main_menu(path=''):

    has_white_icons = getCondVisibility('System.HasAddon("resource.images.studios.white")') == 1
    if has_white_icons:
        icon_path = 'resource://resource.images.studios.white/%(studio)s.png'
        thumb_path = 'resource://resource.images.studios.white/%(studio)s.png'
    else:
        icon_path = 'DefaultAddonMusic.png'
        thumb_path = 'DefaultAddonMusic.png'

    has_coloured_icons = getCondVisibility('System.HasAddon("resource.images.studios.coloured")') == 1
    if has_coloured_icons:
        thumb_path = 'resource://resource.images.studios.coloured/%(studio)s.png'

    radio_items = []
    for channel in CHANNELS:
        icon = icon_path % channel
        thumb = thumb_path % channel
        # url = plugin.url_for(play, name=channel.get('name'))
        url = channel.get('mp3_128')

        item = ListItem(
            label=channel.get('label'),
            label2=channel.get('tagline'),
            iconImage=icon,
            thumbnailImage=thumb,
            path=url,
        )
        item.setArt(dict(thumb=thumb, icon=icon, fanart=icon))
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


if __name__ == '__main__':
    plugin.run()
