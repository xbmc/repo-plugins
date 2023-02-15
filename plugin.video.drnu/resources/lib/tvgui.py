#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
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
import xbmc
import xbmcgui


class AreaSelectorDialog(xbmcgui.WindowDialog):
    def __init__(self, tr, resources_path):
        self.areaSelected = 'none'

        # Background
        background = xbmcgui.ControlImage(0, 0, 1280, 720, str(resources_path/'media/fanart.jpg'))

        title = xbmcgui.ControlLabel(
            0, 60, 1280, 60, "[B]%s[/B][CR]%s" % (tr(30100), tr(30101)), 'font30', alignment=2)

        image_x = 250
        image_y = 250
        y_border = 75
        x_border = 75
        self.drTvButton = xbmcgui.ControlButton(
            x_border, y_border, image_x, image_y, "",
            focusTexture=str(resources_path/'media/button-drtv-focus.png'),
            noFocusTexture=str(resources_path/'media/button-drtv.png')
        )

        self.ramasjangButton = xbmcgui.ControlButton(
            int(1280/2 - x_border - image_x), int(720 - y_border - image_y), image_x, image_y, "",
            focusTexture=str(resources_path/'media/button-ramasjang-focus.png'),
            noFocusTexture=str(resources_path/'media/button-ramasjang.png')
        )

        self.minisjangButton = xbmcgui.ControlButton(
            int(1280/2 + x_border), int(720 - y_border - image_y), image_x, image_y, "",
            focusTexture=str(resources_path/'media/button-minisjang-focus.png'),
            noFocusTexture=str(resources_path/'media/button-minisjang.png')
        )

        self.ultraButton = xbmcgui.ControlButton(
            int(1280 - x_border - image_x), y_border, image_x, image_y, "",
            focusTexture=str(resources_path/'media/button-ultra-focus.png'),
            noFocusTexture=str(resources_path/'media/button-ultra.png')
        )

        self.addControls([
            background,
            title,
            self.drTvButton,
            self.ramasjangButton,
            self.minisjangButton,
            self.ultraButton,
        ])

        self.drTvButton.controlRight(self.ramasjangButton)
        self.drTvButton.controlDown(self.ramasjangButton)
        self.drTvButton.controlLeft(self.ultraButton)

        self.ramasjangButton.controlLeft(self.drTvButton)
        self.ramasjangButton.controlUp(self.drTvButton)
        self.ramasjangButton.controlRight(self.minisjangButton)

        self.minisjangButton.controlLeft(self.ramasjangButton)
        self.minisjangButton.controlUp(self.ultraButton)
        self.minisjangButton.controlRight(self.ultraButton)

        self.ultraButton.controlLeft(self.minisjangButton)
        self.ultraButton.controlDown(self.minisjangButton)
        self.ultraButton.controlRight(self.drTvButton)

        self.setFocus(self.drTvButton)
        self.areaSelected = 'drtv'

        self.id_to_handle = {
            self.drTvButton.getId(): 'drtv',
            self.ramasjangButton.getId(): 'ramasjang',
            self.minisjangButton.getId(): 'minisjang',
            self.ultraButton.getId(): 'ultra',
            }
        xbmc.executebuiltin('AlarmClock(drnuclosedialog, Action(Select) ,00:02, silent, false)')

    def onAction(self, action):
        xbmc.executebuiltin('CancelAlarm(drnuclosedialog, silent)')

    def onControl(self, control):
        self.areaSelected = self.id_to_handle[control.getId()]
        self.close()
