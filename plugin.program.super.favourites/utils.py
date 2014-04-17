#
#       Copyright (C) 2014
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#


import xbmc
import xbmcaddon
import xbmcgui
import os

def GetXBMCVersion():
    #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')

    version = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
    version = version.split('.')
    return int(version[0]), int(version[1]) #major, minor


ADDONID = 'plugin.program.super.favourites'
ADDON   =  xbmcaddon.Addon(ADDONID)
HOME    =  ADDON.getAddonInfo('path')
PROFILE =  os.path.join(ADDON.getAddonInfo('profile'), 'Super Favourites')
VERSION = '1.0.0'
ICON    =  os.path.join(HOME, 'icon.png')
FANART  =  os.path.join(HOME, 'fanart.jpg')
BLANK   =  os.path.join(HOME, 'resources', 'media', 'blank.png')
GETTEXT =  ADDON.getLocalizedString
TITLE   =  GETTEXT(30000)
KEYMAP  = 'super_favourites.xml'

MAJOR, MINOR = GetXBMCVersion()
GOTHAM       = (MAJOR == 13) or (MAJOR == 12 and MINOR == 9)


def DialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    d.ok(TITLE + ' - ' + VERSION, line1, line2 , line3)


def DialogYesNo(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3) == True


def Verify():
    CheckVersion()
    VerifyKeymap()


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        VerifyKeymap()
        

def DeleteKeymap():
    path = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

    tries = 5
    while os.path.exists(path) and tries > 0:
        tries -= 1 
        try: 
            os.remove(path) 
            break 
        except: 
            xbmc.sleep(500)


def VerifyKeymap():
    dest = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

    if os.path.exists(dest):
        return

    key = ADDON.getSetting('HOTKEY').lower()

    if key not in ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']:
        DeleteKeymap()
        xbmc.sleep(1000)
        xbmc.executebuiltin('Action(reloadkeymaps)')  
        return
    
    cmd = '<keymap><Global><keyboard><%s>XBMC.RunAddon(plugin.program.super.favourites)</%s></keyboard></Global></keymap>'  % (key, key)

    f = open(dest, mode='w')
    f.write(cmd)
    f.close()
    xbmc.sleep(1000)

    tries = 4
    while not os.path.exists(dest) and tries > 0:
        tries -= 1
        f = open(dest, mode='w')
        f.write(t)
        f.close()
        xbmc.sleep(1000)
    
    xbmc.executebuiltin('Action(reloadkeymaps)')  


if __name__ == '__main__':
    pass