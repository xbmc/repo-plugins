
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

ACTION_LEFT  = 1
ACTION_RIGHT = 2
ACTION_UP    = 3
ACTION_DOWN  = 4


class ImageBrowser(xbmcgui.WindowXMLDialog):

    def __new__(cls, addonID, items):
        return super(ImageBrowser, cls).__new__(cls, 'imagebrowser.xml', xbmcaddon.Addon(addonID).getAddonInfo('path'))

        

    def __init__(self, addonID, items):
        super(ImageBrowser, self).__init__()
        self.items = items

        
    def onInit(self):
        self.list  = self.getControl(3000)
        self.icon  = self.getControl(3002)
        self.image = ''

        for item in self.items:
            title = item
            liz   = xbmcgui.ListItem(title)
            self.list.addItem(liz)

        self.setFocus(self.list)

           
    def onAction(self, action):
        actionId = action.getId()

        if actionId in [ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_BACK]:
            return self.close()

        self.refreshImage()


    def onClick(self, controlId):        
        if controlId != 3001:
            index = self.list.getSelectedPosition()        

            try:    self.image = self.items[index] + '.png'
            except: pass

        self.close()
        

    def onFocus(self, controlId):
        self.refreshImage()


    def refreshImage(self):
        index = self.list.getSelectedPosition()        

        try:    name = self.items[index] + '.png'
        except: return

        self.icon.setImage(name)


def getImage(addonID, items):
    dialog = ImageBrowser(addonID, items)
    dialog.doModal()
    image = dialog.image
    del dialog
    return image