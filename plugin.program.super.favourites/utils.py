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
import re


def GetXBMCVersion():
    #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')

    version = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
    version = version.split('.')
    return int(version[0]), int(version[1]) #major, minor


def GETTEXT(id):
    text = ADDON.getLocalizedString(id)
    name = ADDON.getLocalizedString(30121)

    if name == DISPLAY:
        return text
    text = text.replace(name, DISPLAY)
    return text


ADDONID = 'plugin.program.super.favourites'
ADDON   =  xbmcaddon.Addon(ADDONID)
HOME    =  ADDON.getAddonInfo('path')
ROOT    =  ADDON.getSetting('FOLDER')
PROFILE =  os.path.join(ROOT, 'Super Favourites')
VERSION =  ADDON.getAddonInfo('version')
ICON    =  os.path.join(HOME, 'icon.png')
FANART  =  os.path.join(HOME, 'fanart.jpg')
SEARCH  =  os.path.join(HOME, 'resources', 'media', 'search.png')
DISPLAY = ADDON.getSetting('DISPLAYNAME')
TITLE   =  GETTEXT(30000)



KEYMAP_HOT  = 'super_favourites_hot.xml'
KEYMAP_MENU = 'super_favourites_menu.xml'

MAJOR, MINOR = GetXBMCVersion()
FRODO        = (MAJOR == 12) and (MINOR < 9)
GOTHAM       = (MAJOR == 13) or (MAJOR == 12 and MINOR == 9)

FILENAME     = 'favourites.xml'
FOLDERCFG    = 'folder.cfg'


def log(text):
    try:
        output = '%s V%s : %s' % (TITLE, VERSION, str(text))
        #print output
        xbmc.log(output, xbmc.LOGDEBUG)
    except:
        pass


def DialogOK(line1, line2='', line3=''):
    d = xbmcgui.Dialog()
    d.ok(TITLE + ' - ' + VERSION, line1, line2 , line3)


def DialogYesNo(line1, line2='', line3='', noLabel=None, yesLabel=None):
    d = xbmcgui.Dialog()
    if noLabel == None or yesLabel == None:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3) == True
    else:
        return d.yesno(TITLE + ' - ' + VERSION, line1, line2 , line3, noLabel, yesLabel) == True


def Progress(title, line1 = '', line2 = '', line3 = ''):
    dp = xbmcgui.DialogProgress()
    dp.create(title, line1, line2, line3)
    dp.update(0)
    return dp


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


def CheckVersion():
    try:
        prev = ADDON.getSetting('VERSION')
        curr = VERSION

        if xbmcgui.Window(10000).getProperty('OTT_RUNNING') != 'True':
            VerifyKeymaps()

        if prev == curr:        
            return

        verifySuperSearch()

        ADDON.setSetting('VERSION', curr)

        if prev == '0.0.0' or prev== '1.0.0':
            folder  = xbmc.translatePath(PROFILE)
            if not os.path.isdir(folder):
                try:    os.makedirs(folder) 
                except: pass

        #call showChangeLog like this to workaround bug in openElec
        script = os.path.join(HOME, 'showChangelog.py')
        cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('changelog', script, 0)
        xbmc.executebuiltin(cmd)
    except Exception, e:
        pass


def verifySuperSearch():
    dst = os.path.join(xbmc.translatePath(ROOT), 'Search')
    src = os.path.join(HOME, 'resources', 'Search', FILENAME)

    try:    os.makedirs(dst)
    except: pass

    dst = os.path.join(dst, FILENAME)

    if not os.path.exists(dst):
        try:
            import shutil
            shutil.copyfile(src, dst)
        except:
            pass
        return


    import favourite

    new   = favourite.getFavourites(src, validate=False)
    line1 = GETTEXT(30123)
    line2 = GETTEXT(30124)

    for item in new:
        fave, index, nFaves = favourite.findFave(dst, item[2])
        if index < 0:
            line = line1 % item[0]
            if DialogYesNo(line1=line, line2=line2):
                favourite.addFave(dst, item)


def UpdateKeymaps():
    if ADDON.getSetting('HOTKEY') != GETTEXT(30111): #i.e. not programmable
        DeleteKeymap(KEYMAP_HOT)

    DeleteKeymap(KEYMAP_MENU)
    VerifyKeymaps()

        
def DeleteKeymap(map):
    path = os.path.join(xbmc.translatePath('special://profile/keymaps'), map)
    DeleteFile(path)


def DeleteFile(path):
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
    if ADDON.getSetting('HOTKEY') == GETTEXT(30111): #i.e. programmable
        return False    

    dest = os.path.join(xbmc.translatePath('special://profile/keymaps'), KEYMAP_HOT)

    if os.path.exists(dest):
        return False

    key = ADDON.getSetting('HOTKEY')

    valid = []
    for i in range(30028, 30040):
        valid.append(GETTEXT(i))
    valid.append(GETTEXT(30058))

    includeKey = key in valid

    if not includeKey:
        DeleteKeymap(KEYMAP_HOT)
        return True

    if isATV():
        DialogOK(GETTEXT(30118), GETTEXT(30119))
        return False

    return WriteKeymap(key.lower(), key.lower())


def WriteKeymap(start, end):
    dest = os.path.join(xbmc.translatePath('special://profile/keymaps'), KEYMAP_HOT)
    cmd  = '<keymap><Global><keyboard><%s>XBMC.RunScript(special://home/addons/plugin.program.super.favourites/hot.py)</%s></keyboard></Global></keymap>'  % (start, end)
    
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
    context = ADDON.getSetting('CONTEXT')  == 'true'

    DeleteKeymap(KEYMAP_MENU)

    if not context:        
        return True

    keymap = xbmc.translatePath('special://profile/keymaps')
    src    = os.path.join(HOME, 'resources', 'keymaps', KEYMAP_MENU)
    dst    = os.path.join(keymap, KEYMAP_MENU)

    try:
        if not os.path.isdir(keymap):
            os.makedirs(keymap)
    except:
        pass

    try:
        import shutil
        shutil.copy(src, dst)
    except:
        pass

    return True


def verifyPlayMedia(cmd):
    return True


def verifyPlugin(cmd):
    try:
        plugin = re.compile('plugin://(.+?)/').search(cmd).group(1)

        return xbmc.getCondVisibility('System.HasAddon(%s)' % plugin) == 1

    except:
        pass

    return True


def verifyScript(cmd):
    try:
        script = cmd.split('(', 1)[1].split(',', 1)[0].replace(')', '').replace('"', '')
        script = script.split('/', 1)[0]

        return xbmc.getCondVisibility('System.HasAddon(%s)' % script) == 1

    except:
        pass

    return True


def isATV():
    return xbmc.getCondVisibility('System.Platform.ATV2') == 1


def GetFolder(title):
    default = ROOT
    folder  = xbmc.translatePath(PROFILE)

    if not os.path.isdir(folder):
        os.makedirs(folder) 

    folder = xbmcgui.Dialog().browse(3, title, 'files', '', False, False, default)
    if folder == default:
        return None

    return xbmc.translatePath(folder)


def showBusy():
    busy = None
    try:
        import xbmcgui
        busy = xbmcgui.WindowXMLDialog('DialogBusy.xml', '')
        busy.show()

        try:    busy.getControl(10).setVisible(False)
        except: pass
    except:
        busy = None

    return busy


def showText(heading, text):
    id = 10147

    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)

    win = xbmcgui.Window(id)

    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            retry -= 1
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            return
        except:
            pass


def showChangelog(addonID=None):
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)

        f     = open(ADDON.getAddonInfo('changelog'))
        text  = f.read()
        title = '%s - %s' % (xbmc.getLocalizedString(24054), ADDON.getAddonInfo('name'))

        showText(title, text)

    except:
        pass

if __name__ == '__main__':
    pass