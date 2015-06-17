
#       Copyright (C) 2013-2014
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
import xbmcgui
import xbmcaddon
import os

ACTION_BACK          = 92
ACTION_PARENT_DIR    = 9
ACTION_PREVIOUS_MENU = 10
ACTION_CONTEXT_MENU  = 117
ACTION_C_KEY         = 122

ACTION_LEFT  = 1
ACTION_RIGHT = 2
ACTION_UP    = 3
ACTION_DOWN  = 4


class ContextMenu(xbmcgui.WindowXMLDialog):

    def __new__(cls, addonID, menu, helix):
        if helix:
            return super(ContextMenu, cls).__new__(cls, 'contextmenu_helix.xml', xbmcaddon.Addon(addonID).getAddonInfo('path'))
        else:
            return super(ContextMenu, cls).__new__(cls, 'contextmenu.xml', xbmcaddon.Addon(addonID).getAddonInfo('path'))
        

    def __init__(self, addonID, menu, helix):
        super(ContextMenu, self).__init__()
        self.menu = menu

        
    def onInit(self):
        for i in range(5):
            self.getControl(5001+i).setVisible(False)
            
        nItem = len(self.menu)  
        if nItem > 5:
            nItem = 5
        id = 5000 + nItem
        self.getControl(id).setVisible(True)
            
        self.list      = self.getControl(3000)
        self.params    = None
        self.paramList = []

        for item in self.menu:
            self.paramList.append(item[1])
            title = item[0]
            liz   = xbmcgui.ListItem(title)
            self.list.addItem(liz)

        self.setFocus(self.list)

           
    def onAction(self, action):        
        actionId = action.getId()

        if actionId in [ACTION_CONTEXT_MENU, ACTION_C_KEY]:
            self.params = 0
            #xbmc.sleep(100)
            return self.close()

        if actionId in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_BACK]:
            return self.close()


    def onClick(self, controlId):
        if controlId != 3001:
            index = self.list.getSelectedPosition()        
            try:    self.params = self.paramList[index]
            except: self.params = None

        self.close()
        

    def onFocus(self, controlId):
        pass


def showMenu(addonID, menu, helix=False):
    menu = ContextMenu(addonID, menu, helix)
    menu.doModal()
    params = menu.params
    del menu
    return params


def selectMenu(title, menu):
    options = []
    for option in menu:
        options.append(option[0])

    option = xbmcgui.Dialog().select(title, options)

    if option < 0:
        return -1

    return menu[option][1]