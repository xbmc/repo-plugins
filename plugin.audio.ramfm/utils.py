#       Copyright (C) 2013
#       by Sean Poyser (seanpoyser@gmail.com)
#

import xbmc
import xbmcaddon
import xbmcgui
import os

id = 'plugin.audio.ramfm'

ADDON = xbmcaddon.Addon(id)
        

def getString(id):
    text = ADDON.getLocalizedString(id)  
    if text == '':
        return id
    return text


def log(text):
    xbmc.log('[%s] : %s' % (id, str(text)), xbmc.LOGDEBUG)
    xbmc.log('[%s] : %s' % (id, str(text)))


def getAddonPath():
    return ADDON.getAddonInfo('path')


def getUserdataPath():
    return xbmc.translatePath(ADDON.getAddonInfo('profile'))


def setSetting(setting, value):
    xbmcaddon.Addon(id).setSetting(setting, value)


def getSetting(setting):
    return xbmcaddon.Addon(id).getSetting(setting)


def hideCancelButton():
    xbmc.sleep(250)
    WINDOW_PROGRESS = xbmcgui.Window(10101)
    CANCEL_BUTTON   = WINDOW_PROGRESS.getControl(10)
    CANCEL_BUTTON.setVisible(False)


def ok(title, line1, line2 = 0, line3 = 0):
    dlg = xbmcgui.Dialog()
    dlg.ok(getString(title), getString(line1), getString(line2), getString(line3))


def yesno(title, line1, line2 = 0, line3 = 0, no = 3, yes = 2):
    dlg = xbmcgui.Dialog()
    return dlg.yesno(getString(title), getString(line1), getString(line2), getString(line3), getString(no), getString(yes)) == 1


def progress(title, line1 = 0, line2 = 0, line3 = 0, hide = True):
    dp = xbmcgui.DialogProgress()
    dp.create(getString(title), getString(line1), getString(line2), getString(line3))
    dp.update(0)
    if hide:
        hideCancelButton()
    return dp


def fileBrowse(title, ext):
    default  = getUserdataPath()
    dlg      = xbmcgui.Dialog()
    filename = dlg.browse(1, getString(title), 'files', '.'+ext, False, False, default)

    if filename == default:
        return None

    return filename


def folderBrowse(title):
    default  = getUserdataPath()
    dlg      = xbmcgui.Dialog()
    folder   = dlg.browse(3, getString(title), 'files', '', False, False, default)

    return folder


def createKeymap():
    dest = os.path.join(xbmc.translatePath('special://userdata/keymaps'), 'Ram FM.xml')

    if os.path.exists(dest):
        return

    addonPath = xbmc.translatePath(getAddonPath())
    source    = os.path.join(addonPath, 'Ram FM.xml')

    f = open(source, mode='r')
    t = f.read()
    f.close()

    try:
        f = open(dest, mode='w')
        f.write(t)
        f.close()
    except:
        #problem writing file so just return
        return

    xbmc.sleep(500)
    xbmc.executebuiltin('Action(reloadkeymaps)')                
      

def deleteKeymap():
    dest = os.path.join(xbmc.translatePath('special://userdata/keymaps'), 'Ram FM.xml')
  
    try: 
        os.remove(dest) 
    except: 
        pass 

    xbmc.sleep(500)
    xbmc.executebuiltin('Action(reloadkeymaps)')                 