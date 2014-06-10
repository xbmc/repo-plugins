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
ROOT    =  ADDON.getSetting('FOLDER')
PROFILE =  os.path.join(ROOT, 'Super Favourites')
VERSION = '1.0.8'
ICON    =  os.path.join(HOME, 'icon.png')
FANART  =  os.path.join(HOME, 'fanart.jpg')
SEARCH  =  os.path.join(HOME, 'resources', 'media', 'search.png')
GETTEXT =  ADDON.getLocalizedString
TITLE   =  GETTEXT(30000)


KEYMAP_HOT  = 'super_favourites_hot.xml'
KEYMAP_MENU = 'super_favourites_menu.xml'

MAJOR, MINOR = GetXBMCVersion()
FRODO        = (MAJOR == 12) and (MINOR < 9)
GOTHAM       = (MAJOR == 13) or (MAJOR == 12 and MINOR == 9)

FILENAME     = 'favourites.xml'
FOLDERCFG    = 'folder.cfg'


def DialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    d.ok(TITLE + ' - ' + VERSION, line1, line2 , line3)


def DialogYesNo(line1, line2='', line3='', noLabel=None, yesLabel=None):
    d = xbmcgui.Dialog()
    if noLabel == None or yesLabel == None:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3) == True
    else:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3, noLabel, yesLabel) == True


def generateMD5(text):
    if not text:
        return ''

    try:
        import hashlib        
        return hashlib.md5(text).hexdigest()
    except:
        pass

    try:
        import md5
        return md5.new(text).hexdigest()
    except:
        pass
        
    return '0'


#def Verify():
#    CheckVersion()
#    VerifyKeymaps()


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    VerifyKeymaps()

    if prev == curr:        
        return

    ADDON.setSetting('VERSION', curr)

    verifySuperSearch(replace=False)

    if prev == '0.0.0' or prev== '1.0.0':
        folder  = xbmc.translatePath(PROFILE)
        if not os.path.isdir(folder):
            os.makedirs(folder) 


def verifySuperSearch(replace=False):
    dst = os.path.join(xbmc.translatePath(ROOT), 'Search', FILENAME)

    if (not replace) and os.path.exists(dst):
        return

    src = os.path.join(HOME, 'resources', 'Search', FILENAME)

    try:    os.mkdir(os.path.join(xbmc.translatePath(ROOT), 'Search'))
    except: pass

    f = open(src, mode='r')
    t = f.read()
    f.close()

    f = open(dst, mode='w')
    f.write(t)
    f.close()


def UpdateKeymaps():
    DeleteKeymap(KEYMAP_HOT)
    DeleteKeymap(KEYMAP_MENU)
    VerifyKeymaps()

        
def DeleteKeymap(map):
    path = os.path.join(xbmc.translatePath('special://profile/keymaps'), map)

    tries = 5
    while os.path.exists(path) and tries > 0:
        tries -= 1 
        try: 
            os.remove(path) 
            break 
        except: 
            xbmc.sleep(500)


def VerifyKeymaps():
    reload = False

    if VerifyKeymapHot():  reload = True
    if VerifyKeymapMenu(): reload = True

    if not reload:
        return

    xbmc.sleep(1000)
    xbmc.executebuiltin('Action(reloadkeymaps)')  


def VerifyKeymapHot():
    dest = os.path.join(xbmc.translatePath('special://profile/keymaps'), KEYMAP_HOT)

    if os.path.exists(dest):
        return False

    key = ADDON.getSetting('HOTKEY').lower()

    includeKey = key in ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'g']

    if not includeKey:
        DeleteKeymap(KEYMAP_HOT)
        return True

    cmd = '<keymap><Global><keyboard><%s>XBMC.RunScript(special://home/addons/plugin.program.super.favourites/hot.py)</%s></keyboard></Global></keymap>'  % (key, key)
    
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

    return True


def VerifyKeymapMenu():
    dest = os.path.join(xbmc.translatePath('special://profile/keymaps'), KEYMAP_MENU)

    if os.path.exists(dest):
        return False

    context = ADDON.getSetting('CONTEXT')  == 'true'

    if not context:
        DeleteKeymap(KEYMAP_MENU)
        return True

    src = os.path.join(HOME, 'resources', 'keymaps', KEYMAP_MENU)
    dst = os.path.join(xbmc.translatePath('special://profile/keymaps'), KEYMAP_MENU)

    import shutil
    shutil.copy(src, dst)

    return True



def GetFolder(title):
    default = ROOT #ADDON.getAddonInfo('profile')
    folder  = xbmc.translatePath(PROFILE)

    if not os.path.isdir(folder):
        os.makedirs(folder) 

    folder = xbmcgui.Dialog().browse(3, title, 'files', '', False, False, default)
    if folder == default:
        return None

    return xbmc.translatePath(folder)


if __name__ == '__main__':
    pass