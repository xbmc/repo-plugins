# SPDX-License-Identifier: GPL-2.0-or-later
"""Helpers shared by the plugin and the service."""

import xbmc

from resources.lib import api

ADDON_ID = 'plugin.audio.zunradio'
PLUGIN_PREFIX = 'plugin://{}/'.format(ADDON_ID)
HOME_WINDOW = 10000
# Property of the Home window: the plugin asks the service to open the scene. SCENE_PLAY: play
# ZUN radio first if it does not play yet; SCENE_OPEN: open the scene once ZUN radio plays.
SCENE_REQUEST = 'plugin.audio.zunradio.scena'
SCENE_PLAY = 'play'
SCENE_OPEN = 'true'


def log(message, level=xbmc.LOGDEBUG):
    xbmc.log('[{}] {}'.format(ADDON_ID, message), level)


def user_agent(addon):
    kodi = xbmc.getInfoLabel('System.BuildVersion').split(' ')[0] or 'unknown'
    return 'Kodi/{} {}/{}'.format(kodi, ADDON_ID, addon.getAddonInfo('version'))


def fetch_now_playing(addon, timeout=api.TIMEOUT):
    """What is on air now, or None when it cannot be found out."""
    try:
        return api.fetch_now_playing(user_agent(addon), timeout)
    except (OSError, ValueError) as error:
        log('Track information unavailable: {}'.format(error))
        return None


def set_now_playing(item, now_playing, addon):
    """Fill a ListItem with the track on air: artist, title, show as album, cover."""
    icon = addon.getAddonInfo('icon')
    fanart = addon.getAddonInfo('fanart')
    station = addon.getLocalizedString(30000)
    tag = item.getMusicInfoTag()
    if now_playing and now_playing.title:
        tag.setTitle(now_playing.title)
        tag.setArtist(now_playing.artist)
        tag.setAlbum(now_playing.show or station)
        thumb = now_playing.cover or now_playing.show_image or icon
    else:
        tag.setTitle(station)
        tag.setArtist('')
        tag.setAlbum('')
        thumb = icon
    item.setArt({'thumb': thumb, 'icon': icon, 'fanart': fanart})
