#
#       Copyright (C) 2014-2015
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
import sfile


def GetXBMCVersion():
    #xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')

    version = xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')
    version = version.split('.')
    return int(version[0]), int(version[1]) #major, minor eg, 13.9.902


def GETTEXT(id):
    return ADDON.getLocalizedString(id)
    #text = ADDON.getLocalizedString(id)
    #name = ADDON.getLocalizedString(30121)

    #if name == DISPLAY:
    #    return text
    #text = text.replace(name, DISPLAY)
    #return text


ADDONID = 'plugin.program.super.favourites'
ADDON   =  xbmcaddon.Addon(ADDONID)
HOME    =  ADDON.getAddonInfo('path')

ROOT    =  ADDON.getSetting('FOLDER')
if not ROOT:
    ROOT = 'special://profile/addon_data/plugin.program.super.favourites/'

PROFILE =  os.path.join(ROOT, 'Super Favourites')
VERSION =  ADDON.getAddonInfo('version')
ICON    =  os.path.join(HOME, 'icon.png')
FANART  =  os.path.join(HOME, 'fanart.jpg')
SEARCH  =  os.path.join(HOME, 'resources', 'media', 'search.png')
DISPLAY =  ADDON.getSetting('DISPLAYNAME')
TITLE   =  GETTEXT(30000)


PLAYABLE = xbmc.getSupportedMedia('video') + '|' + xbmc.getSupportedMedia('music')
PLAYABLE = PLAYABLE.replace('|.zip', '')
#PLAYABLE = 'mp3|mp4|m4v|avi|flv|mpg|mov|txt|%s' % SRC
PLAYABLE = PLAYABLE.split('|')


PLAYMEDIA_MODE      = 1
ACTIVATEWINDOW_MODE = 2
RUNPLUGIN_MODE      = 3
ACTION_MODE         = 4


HOMESPECIAL = 'special://home/'
HOMEFULL    = xbmc.translatePath(HOMESPECIAL)


DEBUG   = ADDON.getSetting('DEBUG') == 'true'


KEYMAP_HOT  = 'super_favourites_hot.xml'
KEYMAP_MENU = 'super_favourites_menu.xml'

MAJOR, MINOR = GetXBMCVersion()
FRODO        = (MAJOR == 12) and (MINOR < 9)
GOTHAM       = (MAJOR == 13) or (MAJOR == 12 and MINOR == 9)
HELIX        = (MAJOR == 14) or (MAJOR == 13 and MINOR == 9)
ISENGARD     = (MAJOR == 15) or (MAJOR == 14 and MINOR == 9)

FILENAME     = 'favourites.xml'
FOLDERCFG    = 'folder.cfg'


def log(text):
    try:
        output = '%s V%s : %s' % (TITLE, VERSION, str(text))
        
        if DEBUG:
            xbmc.log(output)
        else:
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


def LaunchSF():
    xbmc.executebuiltin('ActivateWindow(videos,plugin://%s)' % ADDONID)


def CheckVersion():
    try:
        prev = ADDON.getSetting('VERSION')
        curr = VERSION

        if prev == curr:        
            return

        verifySuperSearch()
        VerifySettinngs()
        VerifyZipFiles()

        src = os.path.join(ROOT, 'cache')
        dst = os.path.join(ROOT, 'C')
        sfile.rename(src, dst)

        ADDON.setSetting('VERSION', curr)

        if prev == '0.0.0' or prev == '1.0.0':
            sfile.makedirs(PROFILE) 

        #call showChangeLog like this to workaround bug in openElec
        script = os.path.join(HOME, 'showChangelog.py')
        cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('changelog', script, 0)
        xbmc.executebuiltin(cmd)
    except:
        pass


def VerifyZipFiles():
    #cleanup corrupt zip files
    sfile.remove(os.path.join('special://userdata', '_sf_temp.zip'))
    sfile.remove(os.path.join('special://userdata', 'SF_Temp'))


def VerifySettinngs():
    #patch any settings that have changed types or values
    if ADDON.getSetting('DISABLEMOVIEVIEW') == 'true':
        ADDON.setSetting('DISABLEMOVIEVIEW', 'false')
        ADDON.setSetting('CONTENTTYPE', '')


def verifySuperSearch():
    old = os.path.join(ROOT, 'Search')
    dst = os.path.join(ROOT, 'S')

    sfile.rename(old, dst)

    try:    sfile.makedirs(dst)
    except: pass

    src = os.path.join(HOME, 'resources', 'search', FILENAME)
    dst = os.path.join(dst, FILENAME)

    if not sfile.exists(dst):
        sfile.copy(src, dst)

    try:
        #patch any changes
        xml = sfile.read(dst)

        xml = xml.replace('is/?action=movies_search&', 'is/?action=movieSearch&')
        xml = xml.replace('is/?action=people_movies&', 'is/?action=moviePerson&')
        xml = xml.replace('is/?action=shows_search&',  'is/?action=tvSearch&')
        xml = xml.replace('is/?action=people_shows&',  'is/?action=tvPerson&')


        f = sfile.file(dst, 'w')
        f.write(xml)            
        f.close()
    except:
        pass

    import favourite

    new = favourite.getFavourites(src, validate=False)

    #line1 = GETTEXT(30123)
    #line2 = GETTEXT(30124)

    for item in new:
        fave, index, nFaves = favourite.findFave(dst, item[2])
        if index < 0:
            #line = line1 % item[0]
            #if DialogYesNo(line1=line, line2=line2):
            favourite.addFave(dst, item)


def UpdateKeymaps():
    if ADDON.getSetting('HOTKEY') != GETTEXT(30111): #i.e. not programmable
        DeleteKeymap(KEYMAP_HOT)

    DeleteKeymap(KEYMAP_MENU)
    VerifyKeymaps()

        
def DeleteKeymap(map):
    path = os.path.join('special://profile/keymaps', map)
    DeleteFile(path)


def DeleteFile(path):
    tries = 5
    while sfile.exists(path) and tries > 0:
        tries -= 1 
        try: 
            sfile.remove(path) 
        except: 
            xbmc.sleep(500)

def verifyLocation():
    #if still set to default location reset, to workaround
    #Android bug in browse folder dialog
    location = ADDON.getSetting('FOLDER')

    profile  = 'special://profile/addon_data/plugin.program.super.favourites/'
    userdata = 'special://userdata/addon_data/plugin.program.super.favourites/'

    if (location == profile) or (location == userdata):
        ADDON.setSetting('FOLDER', '')
        

def verifyPlugins():
    folder = os.path.join(ROOT, 'Plugins')

    if sfile.exists(folder):
        return

    try:    sfile.makedirs(folder)
    except: pass


def VerifyKeymaps():
    reload = False

    if VerifyKeymapHot():
        reload = True

    if VerifyKeymapMenu():
        reload = True

    if not reload:
        return

    xbmc.sleep(1000)
    xbmc.executebuiltin('Action(reloadkeymaps)')  


def VerifyKeymapHot():
    if ADDON.getSetting('HOTKEY') == GETTEXT(30111): #i.e. programmable
        return False    

    dest = os.path.join('special://profile/keymaps', KEYMAP_HOT)

    if sfile.exists(dest):
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
    dest = os.path.join('special://profile/keymaps', KEYMAP_HOT)
    cmd  = '<keymap><Global><keyboard><%s>XBMC.RunScript(special://home/addons/plugin.program.super.favourites/hot.py)</%s></keyboard></Global></keymap>'  % (start, end)
    
    f = sfile.file(dest, 'w')
    f.write(cmd)
    f.close()
    xbmc.sleep(1000)

    tries = 4
    while not sfile.exists(dest) and tries > 0:
        tries -= 1
        f = sfile.file(dest, 'w')
        f.write(cmd)
        f.close()
        xbmc.sleep(1000)

    return True


def VerifyKeymapMenu():
    context = ADDON.getSetting('CONTEXT')  == 'true'

    if not context:
        DeleteKeymap(KEYMAP_MENU)
        return True

    keymap = 'special://profile/keymaps'
    dst    = os.path.join(keymap, KEYMAP_MENU)

    if sfile.exists(dst):
        return False

    src = os.path.join(HOME, 'resources', 'keymaps', KEYMAP_MENU)

    sfile.makedirs(keymap)
    
    sfile.copy(src, dst)

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

    sfile.makedirs(PROFILE) 

    folder = xbmcgui.Dialog().browse(3, title, 'files', '', False, False, default)
    if folder == default:
        return None

    return folder


html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }


def escape(text):
    return str(''.join(html_escape_table.get(c,c) for c in text))


def unescape(text):
    text = text.replace('&amp;',  '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', '\'')
    text = text.replace('&gt;',   '>')
    text = text.replace('&lt;',   '<')
    return text


def fix(text):
    ret = ''
    for ch in text:
        if ord(ch) < 128:
            ret += ch
    return ret.strip()


def Clean(name):
    import re
    name   = re.sub('\([0-9)]*\)', '', name)

    items = name.split(']')
    name  = ''

    for item in items:
        if len(item) == 0:
            continue

        item += ']'
        item  = re.sub('\[[^)]*\]', '', item)

        if len(item) > 0:
            name += item

    name  = name.replace('[', '')
    name  = name.replace(']', '')
    name  = name.strip()

    while True:
        length = len(name)
        name = name.replace('  ', ' ')
        if length == len(name):
            break

    return name.strip()


def fileSystemSafe(text):
    if not text:
        return None

    text = re.sub('[:\\\\/*?\<>|"]+', '', text)
    text = text.strip()
    if len(text) < 1:
        return  None

    return text


def findAddon(item):
    try:
        try:    addon = re.compile('"(.+?)"').search(item).group(1)
        except: addon = item

        addon = addon.replace('plugin://', '')
        addon = addon.replace('script://', '')
        addon = addon.replace('/', '')
        addon = addon.split('?', 1)[0]        

        if xbmc.getCondVisibility('System.HasAddon(%s)' % addon) == 0:
            addon = None
    except:
        addon = None

    return addon


def getSettingsLabel(addon):
    label = xbmcaddon.Addon(addon).getAddonInfo('name')
    label = fix(label)
    label = label.strip()

    try:
        if len(label) > 0:
            return GETTEXT(30094) % label
    except:
        pass

    return GETTEXT(30094) % GETTEXT(30217)


#logic for setting focus inspired by lambda
def openSettings(addonID, focus=None):
    if not focus:            
        return xbmcaddon.Addon(addonID).openSettings()
    
    try:
        xbmc.executebuiltin('Addon.OpenSettings(%s)' % addonID)

        value1, value2 = str(focus).split('.')

        if FRODO:
            xbmc.executebuiltin('SetFocus(%d)' % (int(value1) + 200))
            xbmc.executebuiltin('SetFocus(%d)' % (int(value2) + 100))
        else:
            xbmc.executebuiltin('SetFocus(%d)' % (int(value1) + 100))
            xbmc.executebuiltin('SetFocus(%d)' % (int(value2) + 200))

    except:
        return



#Remove Tags method from
#http://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string

TAG_RE = re.compile('<.*?>')
def RemoveTags(html):
    return TAG_RE.sub('', html)


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


def showText(heading, text, waitForClose=False):
    id = 10147

    xbmc.executebuiltin('ActivateWindow(%d)' % id)
    xbmc.sleep(100)

    win = xbmcgui.Window(id)

    retry = 50
    while (retry > 0):
        try:
            xbmc.sleep(10)
            win.getControl(1).setLabel(heading)
            win.getControl(5).setText(text)
            retry = 0
        except:
            retry -= 1

    if waitForClose:
        while xbmc.getCondVisibility('Window.IsVisible(%d)' % id) == 1:
            xbmc.sleep(50)


def showChangelog(addonID=None):
    try:
        if addonID:
            ADDON = xbmcaddon.Addon(addonID)
        else: 
            ADDON = xbmcaddon.Addon(ADDONID)

        text  = sfile.read(ADDON.getAddonInfo('changelog'))
        title = '%s - %s' % (xbmc.getLocalizedString(24054), ADDON.getAddonInfo('name'))

        showText(title, text)

    except:
        pass


def getAllPlayableFiles(folder):
    files = {}
 
    _getAllPlayableFiles(folder, files)

    return files


def _getAllPlayableFiles(folder, theFiles):
    current, dirs, files = sfile.walk(folder)

    for dir in dirs:        
        path = os.path.join(current, dir)
        _getAllPlayableFiles(path, theFiles)

    for file in files:
        path = os.path.join(current, file)
        if isPlayable(path):
            size = sfile.size(path)
            theFiles[path] = [path, size]


def isFilePlayable(path):
    try:    return ('.' + sfile.getextension(path) in PLAYABLE)
    except: return False


def isPlayable(path):
    if not sfile.exists(path):
        return False

    if sfile.isfile(path):
        playable = isFilePlayable(path)
        return playable
         
    current, dirs, files = sfile.walk(path)

    for file in files:
        if isPlayable(os.path.join(current, file)):
            return True

    for dir in dirs:        
        if isPlayable(os.path.join(current, dir)):
            return True

    return False



def parseFolder(folder, subfolders=True):
    items = []

    current, dirs, files = sfile.walk(folder)

    if subfolders:
        for dir in dirs:        
            path = os.path.join(current, dir)
            if isPlayable(path):
                items.append([dir, path, False])

    for file in files:
        path = os.path.join(current, file)
        if isPlayable(path):
            items.append([file, path, True])

    return items



def playItems(items, id=-1): 
    if items == None or len(items) < 1:
        return

    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear() 

    resolved = False

    for item in items:
        title     = item[0]
        url       = item[1]
        if len(item) > 2:
            iconImage = item[2]
        else:
            iconImage = ICON

        liz   = xbmcgui.ListItem(title, iconImage=iconImage, thumbnailImage=iconImage)
        liz.setInfo(type='Video', infoLabels={'Title':title})
        pl.add(url, liz)

        if id >= 0 and (not resolved):
            import xbmcplugin
            resolved = True
            xbmcplugin.setResolvedUrl(id, True, liz)
    
    if id == -1:
        xbmc.Player().play(pl)


def convertToHome(text):
    if text.startswith(HOMEFULL):
        text = text.replace(HOMEFULL, HOMESPECIAL)

    return text



if __name__ == '__main__':
    pass