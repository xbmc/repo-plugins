
#       Copyright (C) 2013-
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Progr`am is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
# Script inspired and heavily based on original script.favourites from Ronie and Black at XBMC.org
#
# See Readme for more information on how to use this script



import xbmc
import xbmcgui
import os
import urllib

import utils
import favourite
import sfile

ADDON       = utils.ADDON
HOME        = utils.HOME
PROFILE     = utils.PROFILE
FILENAME    = utils.FILENAME
FOLDERCFG   = utils.FOLDERCFG
ADDONID     = utils.ADDONID
ICON        = utils.ICON
DISPLAYNAME = ADDON.getSetting('DISPLAYNAME') 

INHERIT   = ADDON.getSetting('INHERIT') == 'true'
GETTEXT   = ADDON.getLocalizedString


def getFolderThumb(path):
    cfg   = os.path.join(path, FOLDERCFG)
    thumb = getParam('ICON', cfg)

    if thumb:
        return thumb

    if not INHERIT:
        #return 'DefaultFolder.png'
        return ICON

    faves = favourite.getFavourites(os.path.join(path, FILENAME), 1)   

    if len(faves) < 1:
        return ICON

    thumb = faves[0][1]

    if len(thumb) > 0:
        return thumb

    return ICON


def getParam(param, file):
    try:
        config = []
        param  = param.upper() + '='
        config = sfile.readlines(file)
    except:
        return ''

    for line in config:
        if line.startswith(param):
            return line.split(param, 1)[-1].strip()
    return ''


def GetFave(property, path='', changeTitle=False):
    xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % (property, 'Path'))
    xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % (property, 'Label'))
    xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % (property, 'Icon'))
    xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % (property, 'IsFolder'))


    Main(property, path, changeTitle)

    while xbmcgui.Window(10000).getProperty('Super_Favourites_Chooser') == 'true':
        xbmc.sleep(100)

    xbmc.sleep(500)
    return len(xbmc.getInfoLabel('Skin.String(OTT.Path)')) > 0


class Main:
    def __init__(self, property=None, path='', changeTitle=False):
        xbmcgui.Window(10000).setProperty('Super_Favourites_Chooser', 'true')
        if property:
            self.init(property, path, changeTitle)
        else:
            self._parse_argv()

        faves = self.getFaves()
        MyDialog(faves, self.PROPERTY, self.CHANGETITLE, self.PATH, self.MODE)
        
    
    def _parse_argv(self):
        try:           
            params = dict(arg.split('=') for arg in sys.argv[1].split('&'))          
        except:
            params = {}
                    
        path        = params.get('path',     '')               
        property    = params.get('property', '')
        changeTitle = params.get('changetitle',   '').lower() == 'true'

        path = path.replace('SF_AMP_SF', '&')

        self.init(property, path, changeTitle)


    def init(self, property, path, changeTitle): 
        self.PATH        = path
        self.PROPERTY    = property
        self.CHANGETITLE = changeTitle

        self.MODE = 'folder' if len(self.PATH) > 0 else 'root'

        if self.PATH == 'special://profile/':
            self.MODE = 'xbmc'
            self.FULLPATH = xbmc.translatePath(self.PATH)
        else:                
            self.FULLPATH = xbmc.translatePath(os.path.join(utils.PROFILE, self.PATH))

        self.FULLPATH = urllib.unquote_plus(self.FULLPATH)

                
    def getFaves(self):
        file     = os.path.join(self.FULLPATH, FILENAME).decode('utf-8')
        
        faves = []        

        if self.MODE != 'xbmc':        
            try:    
                current, dirs, files = os.walk(self.FULLPATH).next()

                dirs = sorted(dirs, key=str.lower)

                for dir in dirs:
                    path = os.path.join(self.FULLPATH, dir)
                
                    folderCfg = os.path.join(path, FOLDERCFG)
                    colour    = getParam('COLOUR', folderCfg)
                    thumb     = getFolderThumb(path)

                    label = dir
                
                    if len(colour) > 0:
                        label = '[COLOR %s]%s[/COLOR]' % (colour, label)
                
                    fave = [label, thumb, os.path.join(self.PATH, dir),  True]
                    faves.append(fave)
                
            except Exception, e:
                pass
            
        faves.extend(favourite.getFavourites(file))
        
        return faves
            
            
class MainGui(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.faves       = kwargs.get('faves')
        self.property    = kwargs.get('property')
        self.changeTitle = kwargs.get('changeTitle')
        self.path        = kwargs.get('path')
        self.mode        = kwargs.get('mode')
        
        
    def onInit(self):
        try:
            self.favList = self.getControl(6)
            self.getControl(3).setVisible(False)
        except:
            self.favList = self.getControl(3)

        self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(GETTEXT(30000))

        #the remove item 
        self.favList.addItem(xbmcgui.ListItem(GETTEXT(30100), iconImage='DefaultAddonNone.png'))

        if self.mode != 'xbmc':
            self.addFolderItem()

        if self.mode == 'root':
            self.addXBMCFavouritesItem()

        for fave in self.faves:            
            listitem = xbmcgui.ListItem(fave[0])
            
            listitem.setIconImage(fave[1])
            listitem.setProperty('Icon', fave[1])

            cmd = fave[2]
            if cmd.lower().startswith('activatewindow'):
                cmd = cmd.replace('")', '",return)')

            cmd = favourite.removeSFOptions(cmd)

            listitem.setProperty('Path', cmd)
            
            if len(fave) > 3 and fave[3]:
                listitem.setProperty('IsFolder', 'true')
            
            self.favList.addItem(listitem)
            
        # add a dummy item with no action assigned
        listitem = xbmcgui.ListItem(GETTEXT(30101))
        listitem.setProperty('Path', 'noop')
        self.favList.addItem(listitem)
        self.setFocus(self.favList)


    def addXBMCFavouritesItem(self):
        try:
            fullpath = 'special://profile/'
            thumb    = ''

            label    = GETTEXT(30106) % DISPLAYNAME
            listitem = xbmcgui.ListItem(label)

            listitem.setIconImage(thumb)
            listitem.setProperty('Icon',     thumb)
            listitem.setProperty('Path',     fullpath)
            listitem.setProperty('IsFolder', 'true')

            self.favList.addItem(listitem)


        except Exception, e:
            pass


    def addFolderItem(self):
        path = ''

        if len(self.path) == 0:
            path = GETTEXT(30000)
        else:
            path = self.path.replace(os.sep, '/').rsplit('/', 1)[-1]

        try:
            fullpath = os.path.join(utils.PROFILE, self.path)
            thumb    = getFolderThumb(fullpath) if self.mode != 'root' else ICON

            listitem = xbmcgui.ListItem(path + GETTEXT(30102))
                     
            listitem.setIconImage(thumb)
            listitem.setProperty('Icon',     thumb)
            listitem.setProperty('Path',     self.path)
            listitem.setProperty('IsFolder', 'open')

            self.favList.addItem(listitem)

        except Exception, e:
            pass

        
    def onAction(self, action):
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448):
            if len(self.path) == 0: 
                xbmcgui.Window(10000).setProperty('Super_Favourites_Chooser', 'false')               
                self.close()
                return

            if self.mode == 'xbmc':
                self.changeFolder('')
                return

            path = '/' + self.path.replace(os.sep, '/')
            path = path.rsplit('/', 1)[0]
            path = path[1:]
            self.changeFolder(path)

            
    def onClick(self, controlID):
        if controlID == 6 or controlID == 3:
            num = self.favList.getSelectedPosition()

            if num > 0:
                favPath  = self.favList.getSelectedItem().getProperty('Path')
                favLabel = self.favList.getSelectedItem().getLabel()
                favIcon  = self.favList.getSelectedItem().getProperty('Icon')
                isFolder = self.favList.getSelectedItem().getProperty('IsFolder')

                if favLabel.endswith(GETTEXT(30102)):
                    favLabel = favLabel.replace(GETTEXT(30102), '')

                if isFolder:
                    if isFolder.lower() == 'true':
                        self.changeFolder(favPath)
                        return
                    if isFolder.lower() == 'open':
                        cmd  = 'ActivateWindow(10025,"plugin://'
                        cmd += utils.ADDONID + '/?'
                        cmd += 'label=%s&' % urllib.quote_plus(favLabel)
                        cmd += 'folder=%s' % urllib.quote_plus(favPath)
                        cmd += '",return)'
                        favPath = cmd
                
                if self.changeTitle:
                    keyboard = xbmc.Keyboard(favLabel, xbmc.getLocalizedString(528), False)
                    keyboard.doModal()
                    if (keyboard.isConfirmed()):
                        favLabel = keyboard.getText()
                        
                xbmc.executebuiltin('Skin.SetString(%s,%s)' % ( '%s.%s' % ( self.property, 'Path'),   favPath.decode('string-escape')))
                xbmc.executebuiltin('Skin.SetString(%s,%s)' % ( '%s.%s' % ( self.property, 'Label'), favLabel))
               
                if favIcon:
                    xbmc.executebuiltin('Skin.SetString(%s,%s)' % ('%s.%s' % (self.property, 'Icon'), favIcon))
                    
                if isFolder:
                    xbmc.executebuiltin('Skin.SetString(%s,%s)' % ('%s.%s' % (self.property, 'IsFolder'), 'true'))
                else:
                    xbmc.executebuiltin('Skin.SetString(%s,%s)' % ('%s.%s' % (self.property, 'IsFolder'), 'false'))
                    
            else:
                xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % ( self.property, 'Path'))
                xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % ( self.property, 'Label'))
                xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % ( self.property, 'Icon'))
                xbmc.executebuiltin('Skin.Reset(%s)' % '%s.%s' % ( self.property, 'IsFolder'))

            try:    count = int(xbmcgui.Window(10000).getProperty('Super_Favourites_Count'))
            except: count = 0    
            xbmcgui.Window(10000).setProperty('Super_Favourites_Count', str(count+1))
            xbmcgui.Window(10000).setProperty('Super_Favourites_Chooser', 'false')
                
            xbmc.sleep(300)
            self.close()

                
    def onFocus(self, controlID):
        pass


    def changeFolder(self, path):
        path = path.replace('&', 'SF_AMP_SF')
        cmd = 'RunScript(special://home/addons/%s/chooser.py,property=%s&path=%s&changetitle=%s)' % (ADDONID, self.property, path, self.changeTitle)
        self.close()    
        xbmc.executebuiltin(cmd)

        
def MyDialog(faves, property, changeTitle, path, mode):
    w = MainGui('DialogSelect.xml', HOME, faves=faves, property=property, changeTitle=changeTitle, path=urllib.unquote_plus(path), mode=mode)
    w.doModal()
    del w

    
if __name__ == '__main__':
    Main()