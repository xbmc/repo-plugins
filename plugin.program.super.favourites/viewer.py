
#       Copyright (C) 2015
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

import xbmcgui
import xbmcaddon


class Viewer(xbmcgui.WindowXMLDialog):
    ACTION_EXIT = (9, 10, 247, 275, 61467, 216, 257, 61448)


    def __init__(self, *args, **kwargs):
        pass
        

    def onInit(self):
        self.getControl(1000).setImage(self.fanart)
        self.getControl(1100).setImage(self.thumb)

        self.setFocus(self.getControl(2000))


    def onClick(self, controlId):
        self.close()
        pass


    def onFocus(self, controlId):
        pass


    def onAction(self, action):
        actionId = action.getId()
        buttonId = action.getButtonCode()

        if buttonId in self.ACTION_EXIT or actionId in self.ACTION_EXIT:
            self.close()

        if actionId != 107:
            self.close()


def show(fanart, thumb, addon=None):
    try:
        if addon:
            path = xbmcaddon.Addon(addon).getAddonInfo('path')
        else:
            path = xbmcaddon.Addon().getAddonInfo('path')

        v = Viewer('viewer.xml', path, 'Default')   

        v.fanart = fanart
        v.thumb  = thumb

        v.doModal()
        del v

    except:
        pass