#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os
import re
import sys
import urllib

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path')
addon_name = addon.getAddonInfo('name')

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           log( "obj.%s = %s" % (attr, getattr(obj, attr)))

class cGUI(xbmcgui.WindowXML):
    # view_461_comments.xml   
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXML.__init__(self, *args, **kwargs)
        #xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)   #<--- what's the difference?
        self.listing = kwargs.get("listing")
        
        #log( str(args) )
        #log(sys.argv[1])
        
    def onInit(self):
        
        self.gui_listbox = self.getControl(55)
        #url="plugin://plugin.video.reddit_viewer/?url=plugin%3A%2F%2Fplugin.video.youtube%2Fplay%2F%3Fvideo_id%3D73lsIXzBar0&mode=playVideo"
        #url="http://i.imgur.com/ARdeL4F.mp4"
        listitem = xbmcgui.ListItem(label='..', label2="<", iconImage='DefaultAddon.png')
        #listitem.setInfo( type="Video", infoLabels={ "Title": 'h[1]', "plot": "self.rez", "studio": 'hoster', "votes": "0" } )
        #listitem.setPath(url)
        self.gui_listbox.addItem(listitem)
        
        self.gui_listbox.addItems(self.listing)
        self.setFocus(self.gui_listbox)
        pass

    def onClick(self, controlID):
    
        if controlID == 55:
            num = self.gui_listbox.getSelectedPosition()
            item = self.gui_listbox.getSelectedItem()

            if num == 0:
                #log( "  %d clicked on %d" %(self.pluginhandle, num ) )
                #xbmcplugin.setResolvedUrl(self.pluginhandle, True, item)   #<-- for testing the first item added in onInit() 
                self.close()
            else:
                name = item.getLabel()
                di_url =  item.getProperty('url')
                log( "  clicked on %d  desc=%s url=%s " %( num, item.getProperty('id'), di_url )   )
                if di_url:
                    modes={'listImgurAlbum','playSlideshow','listLinksInComment','playTumblr','playInstagram','playFlickr' }
                    if any(x in di_url for x in modes):
                        #playSlideshow uses xml gui, xbmc.Player() sometimes report an error after 'play'-ing 
                        #   use RunPlugin to avoid this issue
                        log( "  playslideshow"  )
                        xbmc.executebuiltin('RunPlugin(%s)' %di_url )
                    else:
                        #a big thank you to spoyser (http://forum.kodi.tv/member.php?action=profile&uid=103929) for this help
                        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                        pl.clear()
                        pl.add(di_url, item)
                        xbmc.Player().play(pl, windowed=True)
                        #self.close()
                    
                    #xbmcplugin.setResolvedUrl(self.pluginhandle, True, item)
                    #xbmc.executebuiltin('RunPlugin(%s)' %di_url )  #works for showing image(with gui) but doesn't work for videos(Attempt to use invalid handle -1)
                    #xbmc.executebuiltin('RunScript(%s)' %di_url )   #nothing works

                    #xbmc.executebuiltin('RunAddon(plugin.video.reddit_viewer)'  ) #does nothing. adding the parameter produces error(unknown plugin)
                    #xbmc.executebuiltin('ActivateWindow(video,%s)' %di_url )       #Can't find window video   ...#Activate/ReplaceWindow called with invalid destination window: video

                    #dump(item)
                    #for property in dir(item):
                    #    log( "%s: %s" %( property, 'value' ) )
    
        elif controlID == 5:
            pass
        elif controlID == 7:
            pass


class qGUI(xbmcgui.WindowXMLDialog):
    #called by playSlideshow
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        
    image_path=""
    s=0

    def onInit(self):
        self.getControl(3000).setImage(self.image_path)
        self.getControl(3100).setImage(self.image_path)
        self.getControl(3200).setImage(self.image_path)
        self.getControl(3300).setImage(self.image_path)

        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)

    def onAction(self, action):
        #ACTION_PREVIOUS_MENU=10    #ACTION_STOP=13    #AACTION_MOUSE_RIGHT_CLICK = 101   #ACTION_BACKSPACE = 110   ACTION_NAV_BACK = 92
        #ACTION_PAUSE = 12     #ACTION_PREV_ITEM = 15    # ACTION_STOP = 13   #KEY_BUTTON_B = 257   #KEY_BUTTON_BACK = 275 ACTION_PARENT_DIR = 9
        #
        #ACTION_PLAY = 68  KEY_BUTTON_A = 256 ACTION_ENTER = 135 ACTION_MOUSE_LEFT_CLICK = 100 ACTION_CONTEXT_MENU = 117
        if action in [68,256, 135,100]:
            self.cycle_zoom()
            #log("aaaaa go")
        
        if action == 31:  #ACTION_ZOOM_IN = 31
            log("zoom in")
        
        if action == 30:  #ACTION_ZOOM_OUT = 30
            log("zoom out")

        if action in [9, 10,13,92, 101,110,12,15,13,257,275,117]:
            self.close()        
        pass

    def onFocus(self, controlId):
        pass
    
    def cycle_zoom(self):
        if self.s==1:
            self.zoom_top()
        elif self.s==2:
            self.zoom_mid()
        elif self.s==3:
            self.zoom_btm()
        else:
            self.zoom_out()

    def zoom_out(self):
        self.s=1
        self.getControl(3000).setVisible(True)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)
    def zoom_top(self):
        self.s=2
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(True)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(False)
    def zoom_mid(self):
        self.s=3
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(True)
        self.getControl(3300).setVisible(False)
    def zoom_btm(self):
        self.s=4
        self.getControl(3000).setVisible(False)
        self.getControl(3100).setVisible(False)
        self.getControl(3200).setVisible(False)
        self.getControl(3300).setVisible(True)
        

    def onClick(self, controlId):
        #if controlId == 3001:
        self.cycle_zoom()
            
    def closeDialog(self):
        self.close()

class ssGUI(xbmcgui.WindowXMLDialog):
    #credit to The big Picture addon.
    CONTROL_MAIN_IMAGE = 100
    CONTROL_VISIBLE = 102
    CONTROL_ASPECT_KEEP = 103
    CONTROL_ARROWS = 104
    CONTROL_BG = 105
    ACTION_CONTEXT_MENU = [117]
    ACTION_PREVIOUS_MENU = [9, 92, 10]
    ACTION_SHOW_INFO = [11]
    ACTION_EXIT_SCRIPT = [13]
    ACTION_DOWN = [4]
    ACTION_UP = [3]
    ACTION_0 = [58, 18]
    ACTION_PLAY = [79]
    items=[]
    album_name=''
    
    def __init__(self, *args, **kwargs):
        #log("starting ssgui")
        #xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        pass

    def onInit(self):
        self.show_info = True
        self.aspect_keep = True

        self.getControls()
        self.addItems(self.items)

        self.setFocus(self.image_list)
        log('onInit finished')

    def onAction(self, action):
        action_id = action   #action.getId()
        if action_id in self.ACTION_SHOW_INFO:
            log('ACTION_SHOW_INFO: category:' + self.getWindowProperty('Category') )
            self.toggleInfo()  #show/hide description
        elif action_id in self.ACTION_CONTEXT_MENU:
            log('ACTION_CONTEXT_MENU category:' + self.getWindowProperty('Category') )
            self.close()
            #self.download_album()
        elif action_id in self.ACTION_PREVIOUS_MENU:
            log('ACTION_PREVIOUS_MENU: category:' + self.getWindowProperty('Category') )
            self.close()

    def onClick(self, controlId):
        if controlId == self.CONTROL_MAIN_IMAGE:
            self.toggleInfo()

    def getControls(self):
        self.window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        self.image_list = self.getControl(self.CONTROL_MAIN_IMAGE)
        self.arrows_controller = self.getControl(self.CONTROL_ARROWS)
        self.aspect_controller = self.getControl(self.CONTROL_ASPECT_KEEP)
        self.info_controller = self.getControl(self.CONTROL_VISIBLE)
        try:
            self.bg_controller = self.getControl(self.CONTROL_BG)
        except RuntimeError:
            # catch exception with skins which override the xml
            # but are not up2date like Aeon Nox
            self.bg_controller = None

    def addItems(self, items):
        #self.log('addItems:' + str(items ))
        self.image_list.reset()
        for item in items:
            #log('aaaaaa : '+str(item))
            li = xbmcgui.ListItem(
                label=item['title'],
                label2=item['description'],
                iconImage=item['pic']
            )
            li.setProperty(
                'album_title',
                self.album_name   #top left-hand side
            )
            #li.setProperty('album_url', "item.get('album_url')")
            li.setProperty('album_id', "0")
            self.image_list.addItem(li)

    def toggleInfo(self):
        self.show_info = not self.show_info
        self.info_controller.setVisible(self.show_info)

    def toggleAspect(self):
        self.aspect_keep = not self.aspect_keep
        self.aspect_controller.setVisible(self.aspect_keep)

    def getWindowProperty(self, key):
        return self.window.getProperty(key)

    def setWindowProperty(self, key, value):
        return self.window.setProperty(key, value)



def log(message, level=xbmc.LOGNOTICE):
    xbmc.log("reddit_viewer GUI:"+message, level=level)




