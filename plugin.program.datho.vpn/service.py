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



import os
import traceback

import xbmc
from utils import Logger

import config
from config import __language__

KEYMAP  = 'datho_vpn_menu.xml'


def DeleteKeymap():
    path = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

    tries = 5
    while os.path.exists(path) and tries > 0:
        tries -= 1 
        try: 
            os.remove(path) 
            break 
        except: 
            xbmc.sleep(500)


def UpdateKeymap():
    DeleteKeymap()

    if config.ADDON.getSetting('CONTEXT')  == 'true':
        src = os.path.join(config.HOME, 'resources', 'keymaps', KEYMAP)
        dst = os.path.join(xbmc.translatePath('special://userdata/keymaps'), KEYMAP)

        import shutil
        shutil.copy(src, dst)

    xbmc.sleep(1000)
    xbmc.executebuiltin('Action(reloadkeymaps)')  



class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.context = config.ADDON.getSetting('CONTEXT')  == 'true'
        self.context = not self.context
        self.onSettingsChanged()


    def onSettingsChanged(self):
        context = config.ADDON.getSetting('CONTEXT')  == 'true'

        if self.context == context:
            return

        self.context = context
        
        UpdateKeymap()
        

monitor = MyMonitor()


while (not xbmc.abortRequested):
    xbmc.sleep(1000)


del monitor
from lib import vpn

try:
    Logger.log("Service main code executed", Logger.LOG_DEBUG)

    vpnConnector = vpn.VPNConnectorFactory.getConnector()
    ret = vpnConnector.kill(showBusy=True)
except Exception:
    Logger.log("Exception raised while trying to execute service main")
    traceback.print_exc()