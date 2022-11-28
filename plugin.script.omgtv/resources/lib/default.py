# -*- coding: utf-8 -*-

"""
    OMGTV
    Author: OMGTV

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import xbmc, xbmcgui, xbmcaddon

ADDON           = xbmcaddon.Addon()
ADDON_NAME      = ADDON.getAddonInfo("name")
ADDON_ID        = ADDON.getAddonInfo('id')
addon		= xbmcaddon.Addon(ADDON_ID)

BASE_URL        = "https://omgtv.rocks/all/"
EPG_URL        = "https://epg.omgtv.rocks/email/"
help_text       = "The watch@omgtv.rocks address is our default set of channels. After creating an account at https:omgtv.rocks, enter your address to watch your favorite channels."

def installPVR():
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        textbox = xbmcgui.ControlTextBox(200, 900, 1500, 150,  font='font10',textColor='0xFF00FFFF')
        window.addControl(textbox)
        textbox.setText(help_text)
        
        try :
                if not xbmc.getCondVisibility('System.HasAddon(pvr.iptvsimple)'):
                        xbmc.executebuiltin('InstallAddon(pvr.iptvsimple)')
                        
        except Exception as e:
                xbmc.log(str(e), xbmc.LOGDEBUG)

        while not xbmc.getCondVisibility('System.HasAddon(pvr.iptvsimple)') :
                xbmc.sleep(1)

        try:
                if  xbmc.getCondVisibility('System.HasAddon(pvr.iptvsimple)'):
                        
                        
                        
                        textbox.reset()
                        textbox.setVisible(False)
                        window.removeControl(textbox)
                        addon.openSettings()
                        
                        email_text = addon.getSetting(id='email')
                        if email_text != "" and "@" in email_text :
                                PvrEnable	  = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":false},"id":1}'
                                jsonSetPVR	  = '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"pvrmanager.enabled", "value":true},"id":1}'
                                jsonSetEPG	  = '{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"epg.selectaction", "value":1},"id":1}'

                                IPTVon		  = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":true},"id":1}'
                                IPTVoff		  = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.iptvsimple","enabled":false},"id":1}'
                                nulldemo	  = '{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{"addonid":"pvr.demo","enabled":false},"id":1}'
                                urllink	  = BASE_URL + email_text
                                epglink	  = EPG_URL + email_text

                                xbmc.executeJSONRPC(PvrEnable)
                                xbmc.executeJSONRPC(IPTVon)
                                xbmc.executeJSONRPC(nulldemo)
                                xbmc.executeJSONRPC(jsonSetEPG)

                                pvr_addon = xbmcaddon.Addon('pvr.iptvsimple')
                                skindir = xbmc.getSkinDir()
                                skin_addon = xbmcaddon.Addon(skindir)
                                pvr_addon.setSetting(id='m3uPathType', value = "1")
                                pvr_addon.setSetting(id='m3uUrl', value = urllink)
                                pvr_addon.setSetting(id='m3uCache', value = "false")
                                pvr_addon.setSetting(id='epgPathType', value = "1")
                                pvr_addon.setSetting(id='epgUrl', value = epglink)
                                pvr_addon.setSetting(id='epgCache', value = "false")
                                xbmc.executebuiltin("Skin.SetBool(HomeMenuNoTVButton, False)")
                                xbmc.executebuiltin("Skin.SetBool(HomeMenuNoRadioButton, False)")
                                xbmcgui.Dialog().ok(ADDON_NAME,"PVR Client Updated, Kodi needs to re-launch for changes to take effect, click ok to quit kodi and then please re launch")
                                xbmc.executebuiltin("Quit")
                        else :
                               xbmcgui.Dialog().ok(ADDON_NAME,"Wrong email address") 
                        
                        
                else :
                        xbmcgui.Dialog().ok(ADDON_NAME,"PVR Client: Unknown Error")
                
                        
                
        except Exception as e:
                print(" erreur install pvr ",str(e))
                xbmcgui.Dialog().ok(ADDON_NAME,"PVR Client: Unknown Error or PVR already Set-Up")
                

        finally :
                pass 
		


