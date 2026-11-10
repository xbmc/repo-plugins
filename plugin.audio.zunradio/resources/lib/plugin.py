# SPDX-License-Identifier: GPL-2.0-or-later
"""The plugin: list of ZUN radio streams and their playback."""

import sys
from urllib.parse import parse_qsl, urlencode

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib import api, kodiutils, scena

# Short timeout: the user is waiting for the list or for the music
TIMEOUT = 4

# Strings: the visualisation is not available for this device, it is installed already
VIS_UNAVAILABLE = 30107
VIS_INSTALLED = 30108


def run(argv=None):
    argv = argv or sys.argv
    base_url = argv[0]
    handle = int(argv[1])
    params = dict(parse_qsl(argv[2].lstrip('?'))) if len(argv) > 2 else {}
    addon = xbmcaddon.Addon()
    if params.get('action') == 'play':
        play(handle, addon, api.stream_by_id(params.get('stream')))
    elif params.get('action') == 'scena':
        # A folder that lists nothing: Kodi stays in the list and the scene opens. As a file
        # item Kodi put it into the playlist of the songs and skipped it as unplayable.
        xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
        request_scene()
    elif params.get('action') == 'vizualizace':
        # The button in the settings (RunPlugin, no list to fill)
        install_visualisation(addon)
    else:
        list_streams(base_url, handle, addon)


def describe(now_playing, addon):
    """Text about the track and the show on air, for the list of streams."""
    lines = []
    if now_playing and now_playing.title:
        lines.append(addon.getLocalizedString(30010).format(artist=now_playing.artist,
                                                            title=now_playing.title))
    if now_playing and now_playing.show:
        lines.append(addon.getLocalizedString(30011).format(show=now_playing.show))
    lines.append(addon.getLocalizedString(30012))
    return '\n'.join(lines)


def list_streams(base_url, handle, addon):
    now_playing = kodiutils.fetch_now_playing(addon, TIMEOUT)
    comment = describe(now_playing, addon)
    icon = addon.getAddonInfo('icon')
    art = {'icon': icon, 'thumb': icon, 'fanart': addon.getAddonInfo('fanart')}
    for stream in api.STREAMS:
        label = addon.getLocalizedString(stream.label_id)
        item = xbmcgui.ListItem(label=label, offscreen=True)
        item.setProperty('IsPlayable', 'true')
        tag = item.getMusicInfoTag()
        tag.setTitle(label)
        tag.setComment(comment)
        item.setArt(art)
        url = '{}?{}'.format(base_url, urlencode({'action': 'play', 'stream': stream.id}))
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)
    label = addon.getLocalizedString(30004)
    item = xbmcgui.ListItem(label=label, offscreen=True)
    tag = item.getMusicInfoTag()
    tag.setTitle(label)
    tag.setComment(addon.getLocalizedString(30005))
    item.setArt(art)
    xbmcplugin.addDirectoryItem(handle, '{}?action=scena'.format(base_url), item, isFolder=True)
    xbmcplugin.setContent(handle, 'songs')
    xbmcplugin.endOfDirectory(handle)


def play(handle, addon, stream):
    item = xbmcgui.ListItem(path=stream.url, offscreen=True)
    item.setMimeType(stream.mimetype)
    item.setContentLookup(False)
    kodiutils.set_now_playing(item, kodiutils.fetch_now_playing(addon, TIMEOUT), addon)
    xbmcplugin.setResolvedUrl(handle, True, item)


def install_visualisation(addon):
    """Install visualization.zunradio where a repository offers it for this device, else say so.

    Binary add-ons are built per platform and not every repository has them (LibreELEC and
    CoreELEC build their own), so a plain InstallAddon would fail without a word there.
    Kodi itself asks before it installs.
    """
    if xbmc.getCondVisibility('System.HasAddon({})'.format(scena.VIS_ID)):
        message = VIS_INSTALLED
    elif scena.vis_in_repository():
        xbmc.executebuiltin('InstallAddon({})'.format(scena.VIS_ID), True)
        return
    else:
        message = VIS_UNAVAILABLE
    xbmcgui.Dialog().ok(addon.getLocalizedString(30000), addon.getLocalizedString(message))


def request_scene():
    """Ask the service for the scene; the service plays ZUN radio first when it does not play.

    No playback from here: this runs while Kodi waits for the list with its busy dialog, and
    playing a plugin path opens a second one. Kodi 20 then exits ("Logic error due to two
    concurrent busydialogs", bedroom RPi4 2026-11-08 and 2026-11-10); Kodi 21 copes.
    """
    xbmcgui.Window(kodiutils.HOME_WINDOW).setProperty(kodiutils.SCENE_REQUEST, kodiutils.SCENE_PLAY)
