# -*- coding: utf-8 -*-
from __future__ import absolute_import

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

ADDON = xbmcaddon.Addon()
tr = ADDON.getLocalizedString

def get_profile_path(rpath):
    return xbmc.translatePath(ADDON.getAddonInfo('profile') + rpath)

def load_channel_subs():
    channels = []
    try:
        f = xbmcvfs.File(get_profile_path('channel_subs'), 'r')
        lines = f.readBytes()
        f.close()
    except Exception as e:
        pass
    lines = lines.decode('utf-8')
    for line in lines.split('\n'):
        items = line.split('#')
        if len(items) < 2:
            continue
        channels.append((items[0],items[1]))
    return channels

def save_channel_subs(channels):
    try:
        f = xbmcvfs.File(get_profile_path('channel_subs'), 'w')
        for (name, claim_id) in channels:
            f.write(bytearray(name.encode('utf-8')))
            f.write('#')
            f.write(bytearray(claim_id.encode('utf-8')))
            f.write('\n')
        f.close()
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)

def load_playlist(name):
    items = []
    try:
        f = xbmcvfs.File(get_profile_path(name + '.list'), 'r')
        lines = f.readBytes()
        f.close()
    except Exception as e:
        pass
    lines = lines.decode('utf-8')
    for line in lines.split('\n'):
        if line != '':
            items.append(line)
    return items

def save_playlist(name, items):
    try:
        f = xbmcvfs.File(get_profile_path(name + '.list'), 'w')
        for item in items:
            f.write(bytearray(item.encode('utf-8')))
            f.write('\n')
        f.close()
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)
