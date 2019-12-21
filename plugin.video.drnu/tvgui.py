#
#      Copyright (C) 2014 Tommy Winther, msj33
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os

import xbmcaddon
import xbmcgui


class AreaSelectorDialog(xbmcgui.WindowDialog):
    def __init__(self):
        self.areaSelected = 'none'

        ADDON = xbmcaddon.Addon()

        # Background
        background = xbmcgui.ControlImage(0, 0, 1280, 720, os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg'))

        title = xbmcgui.ControlLabel(0, 60, 1280, 60, "[B]%s[/B][CR]%s" % (ADDON.getLocalizedString(30100), ADDON.getLocalizedString(30101)), 'font30', alignment=2)

        self.drTvButton = xbmcgui.ControlButton(20, 160, 400, 400, "",
                                                focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-drtv-focus.png'),
                                                noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-drtv.png')
                                                )

        self.ramasjangButton = xbmcgui.ControlButton(440, 160, 400, 400, "",
                                                     focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ramasjang-focus.png'),
                                                     noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ramasjang.png')
                                                     )

        self.ultraButton = xbmcgui.ControlButton(860, 160, 400, 400, "",
                                                 focusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ultra-focus.png'),
                                                 noFocusTexture=os.path.join(ADDON.getAddonInfo('path'), 'resources', 'button-ultra.png')
                                                 )

        self.addControls([background, title, self.drTvButton, self.ramasjangButton, self.ultraButton])

        self.drTvButton.controlRight(self.ramasjangButton)
        self.drTvButton.controlLeft(self.ultraButton)
        self.ramasjangButton.controlLeft(self.drTvButton)
        self.ramasjangButton.controlRight(self.ultraButton)
        self.ultraButton.controlLeft(self.ramasjangButton)
        self.ultraButton.controlRight(self.drTvButton)

        self.setFocus(self.drTvButton)

    def onControl(self, control):
        if control == self.drTvButton:
            self.areaSelected = 'drtv'
        elif control == self.ramasjangButton:
            self.areaSelected = 'ramasjang'
        elif control == self.ultraButton:
            self.areaSelected = 'ultra'

        self.close()
