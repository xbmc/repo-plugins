# -*- coding: utf-8 -*-
from __future__ import absolute_import

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui

ADDON = xbmcaddon.Addon()
tr = ADDON.getLocalizedString

def get_profile_path(rpath):
    return xbmcvfs.translatePath(ADDON.getAddonInfo('profile') + rpath)

def create_profile_directory_if_missing():
    profile_path = ADDON.getAddonInfo('profile')
    if not xbmcvfs.exists(profile_path):
        xbmcvfs.mkdir(profile_path)

def open_file(name, mode):
    if mode == 'w':
        create_profile_directory_if_missing()
    return xbmcvfs.File(get_profile_path(name), mode)

def load_channel_subs():
    channels = []
    try:
        with open_file('channel_subs', 'r') as f:
            lines = f.readBytes().decode('utf-8')
            for line in lines.split('\n'):
                items = line.split('#')
                if len(items) < 2:
                    continue
                channels.append((items[0],items[1]))
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)
    return channels

def save_channel_subs(channels):
    try:
        with open_file('channel_subs', 'w') as f:
            for (name, claim_id) in channels:
                f.write(bytearray(name.encode('utf-8')))
                f.write('#')
                f.write(bytearray(claim_id.encode('utf-8')))
                f.write('\n')
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)

def load_playlist(name):
    items = []
    try:
        with open_file(name + '.list', 'r') as f:
            lines = f.readBytes().decode('utf-8')
            for line in lines.split('\n'):
                if line != '':
                    items.append(line)
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)
    return items

def save_playlist(name, items):
    try:
        with open_file(name + '.list', 'w') as f:
            for item in items:
                f.write(bytearray(item.encode('utf-8')))
                f.write('\n')
    except Exception as e:
        xbmcgui.Dialog().notification(tr(30104), str(e), xbmcgui.NOTIFICATION_ERROR)
