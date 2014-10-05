#
#       Copyright (C) 2014 Datho Digital Inc
#       Martin Candurra (martincandurra@dathovpn.com)
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

import gui
import config
from utils import Logger
from config import __language__

def CheckVersion():
    prev = config.ADDON.getSetting('VERSION')
    curr = config.VERSION

    msg = __language__(30043) % config.VERSION

    Logger.log(msg, Logger.LOG_ERROR)

    if prev == curr:
        return

    config.ADDON.setSetting('VERSION', curr)


    if prev == '0.0.0':
        gui.DialogOK(msg)


def CheckUsername():
    if config.CheckCredentialsEmpty():
        gui.DialogOK(__language__(30044))
        gui.ShowSettings()

