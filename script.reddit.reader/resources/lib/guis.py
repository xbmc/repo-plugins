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
from xbmcgui import ControlButton
#import xbmcplugin

addon = xbmcaddon.Addon()
addon_path = addon.getAddonInfo('path')
addon_name = addon.getAddonInfo('name')

def dump(obj):
    for attr in dir(obj):
        if hasattr( obj, attr ):
            log( "obj.%s = %s" % (attr, getattr(obj, attr)))

class cGUI(xbmcgui.WindowXML):
    # view_461_comments.xml   
    include_parent_directory_entry=True
    title_bar_text=""
    gui_listbox_SelectedPosition=0
    
    #plot_font="a" #font used for 'plot' <- where the image or comment description is stored ### cannot set font size.
    #CONTROL_ID_FOR_PLOT_TEXTBOX=65591
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXML.__init__(self, *args, **kwargs)
        #xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)   #<--- what's the difference?
        self.subreddits_file = kwargs.get("subreddits_file")
        self.listing = kwargs.get("listing")
        self.main_control_id = kwargs.get("id")
        
        #log( str(args) )
        #log(sys.argv[1])
        
    def onInit(self):
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        self.gui_listbox = self.getControl(self.main_control_id)
        #important to reset the listbox. when control comes back to this GUI(after calling another gui). 
        #  kodi will "onInit" this GUI again. we end up adding items in gui_listbox
        self.gui_listbox.reset()
        
        if self.title_bar_text:
            self.ctl_title_bar = self.getControl(1)
            self.ctl_title_bar.setLabel(self.title_bar_text)
            
        # will not work. 'xbmcgui.ControlTextBox' does not have methods to set font size
        # it might be possible to make the textbox control in code and addcontrol() it. but then you would have to figure out how to get text to change when listbox selection changes.   
        #if self.plot_font:
        #    self.ctl_plot_textbox = self.getControl(self.CONTROL_ID_FOR_PLOT_TEXTBOX)
        #    self.ctl_plot_textbox.setLabel('Status', 'font14', '0xFFFFFFFF', '0xFFFF3300', '0xFF000000')
            
        #url="plugin://plugin.video.reddit_viewer/?url=plugin%3A%2F%2Fplugin.video.youtube%2Fplay%2F%3Fvideo_id%3D73lsIXzBar0&mode=playVideo"
        #url="http://i.imgur.com/ARdeL4F.mp4"
        if self.include_parent_directory_entry:
            back_image='DefaultFolderBackSquare.png'
            listitem = xbmcgui.ListItem(label='..', label2="", iconImage=back_image)
            #listitem.setInfo( type="Video", infoLabels={ "Title": '..', "plot": "", "studio": '' } )
            listitem.setArt({"thumb": back_image }) #, "poster":back_image, "banner":back_image, "fanart":back_image, "landscape":back_image   })
            #listitem.setPath(url)
            self.gui_listbox.addItem(listitem)
        
        self.gui_listbox.addItems(self.listing)
        self.setFocus(self.gui_listbox)
        
        if self.gui_listbox_SelectedPosition > 0:
            self.gui_listbox.selectItem( self.gui_listbox_SelectedPosition )
        
        pass
    

    def onClick(self, controlID):
        
        if controlID == self.main_control_id:
            self.gui_listbox_SelectedPosition = self.gui_listbox.getSelectedPosition()
            item = self.gui_listbox.getSelectedItem()

            if self.include_parent_directory_entry and self.gui_listbox_SelectedPosition == 0: 
                self.close()  #include_parent_directory_entry means that we've added a ".." as the first item on the list onInit

            #name = item.getLabel()
            try:di_url=item.getProperty('onClick_action') #this property is created when assembling the kwargs.get("listing") for this class
            except:di_url=""
            item_type=item.getProperty('item_type').lower()
            
            log( "  clicked on %d IsPlayable=%s  url=%s " %( self.gui_listbox_SelectedPosition, item_type, di_url )   )
            if item_type=='playable':
                    #a big thank you to spoyser (http://forum.kodi.tv/member.php?action=profile&uid=103929) for this help
                    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                    pl.clear()
                    pl.add(di_url, item)
                    xbmc.Player().play(pl, windowed=False)
                    #self.close()
            elif item_type=='script':
                #"script.web.viewer, http://m.reddit.com/login"
                #log(  di_url )
                xbmc.executebuiltin("ActivateWindow(busydialog)")
                xbmc.executebuiltin( di_url  )
                xbmc.sleep(5000)
                xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                
                #modes=['listImgurAlbum','viewImage','listLinksInComment','playTumblr','playInstagram','playFlickr' ]
                #if any(x in di_url for x in modes):
                    #viewImage uses xml gui, xbmc.Player() sometimes report an error after 'play'-ing 
                    #   use RunPlugin to avoid this issue
                    

                
                #xbmcplugin.setResolvedUrl(self.pluginhandle, True, item)
                #xbmc.executebuiltin('RunPlugin(%s)' %di_url )  #works for showing image(with gui) but doesn't work for videos(Attempt to use invalid handle -1)
                #xbmc.executebuiltin('RunScript(%s)' %di_url )   #nothing works

                #xbmc.executebuiltin('RunAddon(plugin.video.reddit_viewer)'  ) #does nothing. adding the parameter produces error(unknown plugin)
                #xbmc.executebuiltin('ActivateWindow(video,%s)' %di_url )       #Can't find window video   ...#Activate/ReplaceWindow called with invalid destination window: video

        elif controlID == 5:
            pass
        elif controlID == 7:
            pass

    def load_subreddits_file_into_a_listitem(self):
        from utils import parse_subreddit_entry, build_script, compose_list_item, assemble_reddit_filter_string, prettify_reddit_query
        entries=[]
        listing=[]
        
        if os.path.exists(self.subreddits_file):
            fh = open(self.subreddits_file, 'r')
            content = fh.read()
            fh.close()
            spl = content.split('\n')
            
            for i in range(0, len(spl), 1):
                if spl[i]:
                    subreddit = spl[i].strip()
                    entries.append(subreddit )
        entries.sort()
        #log( '  entries count ' + str( len( entries) ) )

        for subreddit_entry in entries:
            #strip out the alias identifier from the subreddit string retrieved from the file so we can process it.
            subreddit, alias, shortcut_description=parse_subreddit_entry(subreddit_entry)
            #log( subreddit + "   " + shortcut_description )
        
            reddit_url= assemble_reddit_filter_string("",subreddit, "yes")
    
            liz = compose_list_item( alias, "", "", "script", build_script("listSubReddit",reddit_url,prettify_reddit_query(alias)) )
            liz.setProperty('ACTION_manage_subreddits', build_script('manage_subreddits', subreddit_entry,"","" ) )
        
            listing.append(liz)
            
        return listing       
        
    def busy_execute_sleep(self,executebuiltin, sleep=500, close=True):
        #
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        #RunAddon(script.reddit.reader,mode=listSubReddit&url=https%3A%2F%2Fwww.reddit.com%2Fr%2Fall%2F.json%3F%26nsfw%3Ano%2B%26limit%3D10%26after%3Dt3_4wmiag&name=all&type=)
        xbmc.executebuiltin( executebuiltin  )
        xbmc.sleep(sleep) #a sleep of 500 is enough for listing subreddit  use about 5000 for executing a link/playing video especially a ytdl video
        if close:
            self.close()
        else:
            xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        pass

class indexGui(cGUI):
    #this is the gui that handles the initial screen. 
    
    def onInit(self):
        #cGui.onInit()
        self.gui_listbox = self.getControl(self.main_control_id)
        #important to reset the listbox. when control comes back to this GUI(after calling another gui). 
        #  kodi will "onInit" this GUI again. we end up adding items in gui_listbox
        self.gui_listbox.reset()
        
        if self.title_bar_text:
            self.ctl_title_bar = self.getControl(1)
            self.ctl_title_bar.setLabel(self.title_bar_text)
            
        #load subreddit file directly here instead of the function that calls the gui.
        #   that way, this gui can refresh the list after the subreddit file modified
        self.gui_listbox.addItems( self.load_subreddits_file_into_a_listitem() )
            
        #self.setFocus(self.gui_listbox)
        
        if self.gui_listbox_SelectedPosition > 0:
            self.gui_listbox.selectItem( self.gui_listbox_SelectedPosition )
        
        pass
    
    
    def onAction(self, action):

        if action in [ xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK ]:
            self.close()

        try:focused_control=self.getFocusId()
        except:focused_control=0

        if focused_control==self.main_control_id:  #main_control_id is the listbox
        
            self.gui_listbox_SelectedPosition  = self.gui_listbox.getSelectedPosition()
            item = self.gui_listbox.getSelectedItem()

            item_type   =item.getProperty('item_type').lower()
                        
            if action == xbmcgui.ACTION_MOVE_LEFT:
                ACTION_manage_subreddits=item.getProperty('ACTION_manage_subreddits')
                log( "   left pressed  %d IsPlayable=%s  url=%s " %(  self.gui_listbox_SelectedPosition, item_type, ACTION_manage_subreddits )   )
                #xbmc.executebuiltin("ActivateWindow(busydialog)")

                
                xbmc.executebuiltin( ACTION_manage_subreddits  )
                
                self.close()
                #xbmc.sleep(2000)
                #xbmc.executebuiltin( "Dialog.Close(busydialog)" )
                
            if action == xbmcgui.ACTION_MOVE_RIGHT:
                right_button_action=item.getProperty('right_button_action')    
                
                log( "   RIGHT pressed  %d IsPlayable=%s  url=%s " %(  self.gui_listbox_SelectedPosition, item_type, right_button_action )   )
    
    
class listSubRedditGUI(cGUI):
    reddit_query_of_this_gui=''
    SUBREDDITS_LIST=550
    SIDE_SLIDE_PANEL=9000
    #all controls in the side panel needs to be included in focused_control ACTION_MOVE_RIGHT check
    BTN_GOTO_SUBREDDIT=6052
    BTN_ZOOM_N_SLIDE=6053
    BTN_PLAY_ALL=6054
    BTN_SLIDESHOW=6055
    BTN_PLAY_FROM_HERE=6057
    
    def onInit(self):
        cGUI.onInit(self)
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

        self.subreddits_listbox = self.getControl(self.SUBREDDITS_LIST)
        self.subreddits_listbox.reset()

        self.subreddits_listbox.addItems( self.load_subreddits_file_into_a_listitem() )

        pass
    
    def onAction(self, action):
        
        
        if action in [ xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK ]:
            self.close()

        try:focused_control=self.getFocusId()
        except:focused_control=0
        #log( "  onAction focused control=" +  str(focused_control) + " " + str( self.a ))
        
        if focused_control==self.main_control_id:  #main_control_id is the listbox
        
            self.gui_listbox_SelectedPosition  = self.gui_listbox.getSelectedPosition()
            item = self.gui_listbox.getSelectedItem()

            item_type   =item.getProperty('item_type').lower()
            
                        
            if action == xbmcgui.ACTION_MOVE_LEFT:
                #show side menu panel
                self.setFocusId(self.SIDE_SLIDE_PANEL)
                
                #right_button_action=item.getProperty('right_button_action')    
                #log( "   LEFT pressed  %d IsPlayable=%s  url=%s " %(  self.gui_listbox_SelectedPosition, item_type, right_button_action )   )
                #xbmc.executebuiltin( right_button_action  )
                
                #xbmc.executebuiltin( "RunAddon(script.reddit.reader, ?mode=zoom_n_slide&url=d:\\test4.jpg&name=2988&type=5312)"  )
                #xbmc.executebuiltin( "RunAddon(script.reddit.reader, ?mode=molest_xml)"  )
                
            if action == xbmcgui.ACTION_MOVE_RIGHT:
                comments_action=item.getProperty('comments_action')
                log( "   RIGHT(comments) pressed  %d IsPlayable=%s  url=%s " %(  self.gui_listbox_SelectedPosition, item_type, comments_action )   )
                if comments_action:
                    #if there are no comments, the comments_action property is not created for this listitem
                    self.busy_execute_sleep(comments_action,3000,False )
                

        if focused_control in [self.SIDE_SLIDE_PANEL,self.SUBREDDITS_LIST,self.BTN_GOTO_SUBREDDIT,self.BTN_ZOOM_N_SLIDE,self.BTN_SLIDESHOW]:   
            if action == xbmcgui.ACTION_MOVE_RIGHT:
                self.setFocusId(self.main_control_id)

            if action == xbmcgui.ACTION_MOVE_LEFT and focused_control==self.SUBREDDITS_LIST :
                item = self.subreddits_listbox.getSelectedItem()
                ACTION_manage_subreddits=item.getProperty('ACTION_manage_subreddits')
                #log( "   left pressed  %d  url=%s " %(  self.gui_listbox_SelectedPosition, ACTION_manage_subreddits )   )
                #xbmc.executebuiltin("ActivateWindow(busydialog)")
                
                self.busy_execute_sleep(ACTION_manage_subreddits, 50, True)
                #xbmc.executebuiltin( ACTION_manage_subreddits  )
                #self.close()
        pass 

    def onClick(self, controlID):
        from utils import build_script
        #log( ' clicked on control id %d'  %controlID )
        
        listbox_selected_item=self.gui_listbox.getSelectedItem()
        subreddits_selected_item=self.subreddits_listbox.getSelectedItem()
        
        if controlID == self.main_control_id:
            self.gui_listbox_SelectedPosition = self.gui_listbox.getSelectedPosition()
            #item = self.gui_listbox.getSelectedItem()

            if self.include_parent_directory_entry and self.gui_listbox_SelectedPosition == 0: 
                self.close()  #include_parent_directory_entry means that we've added a ".." as the first item on the list onInit

            #name = item.getLabel()
            try:di_url=listbox_selected_item.getProperty('onClick_action') #this property is created when assembling the kwargs.get("listing") for this class
            except:di_url=""
            item_type=listbox_selected_item.getProperty('item_type').lower()
            
            log( "  clicked on %d IsPlayable=%s  url=%s " %( self.gui_listbox_SelectedPosition, item_type, di_url )   )
            if item_type=='playable':
                    #a big thank you to spoyser (http://forum.kodi.tv/member.php?action=profile&uid=103929) for this help
                    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                    pl.clear()
                    pl.add(di_url, listbox_selected_item)
                    xbmc.Player().play(pl, windowed=False)
                    #self.close()
            elif item_type=='script':
                #"script.web.viewer, http://m.reddit.com/login"
                #log(  di_url )

                #if user clicked on 'next' we close this screen and load the next page. 
                if 'mode=listSubReddit' in di_url:
                    self.busy_execute_sleep(di_url,500,True )
                else:
                    self.busy_execute_sleep(di_url,5000,False )
                
                #modes=['listImgurAlbum','viewImage','listLinksInComment','playTumblr','playInstagram','playFlickr' ]
                #if any(x in di_url for x in modes):
                    #viewImage uses xml gui, xbmc.Player() sometimes report an error after 'play'-ing 
                    #   use RunPlugin to avoid this issue
                    

                
                #xbmcplugin.setResolvedUrl(self.pluginhandle, True, item)
                #xbmc.executebuiltin('RunPlugin(%s)' %di_url )  #works for showing image(with gui) but doesn't work for videos(Attempt to use invalid handle -1)
                #xbmc.executebuiltin('RunScript(%s)' %di_url )   #nothing works

                #xbmc.executebuiltin('RunAddon(plugin.video.reddit_viewer)'  ) #does nothing. adding the parameter produces error(unknown plugin)
                #xbmc.executebuiltin('ActivateWindow(video,%s)' %di_url )       #Can't find window video   ...#Activate/ReplaceWindow called with invalid destination window: video

    
        elif controlID == self.SUBREDDITS_LIST:
            di_url=subreddits_selected_item.getProperty('onClick_action') #this property was created in load_subreddits_file_into_a_listitem 
            self.busy_execute_sleep(di_url )
            pass
        elif controlID == self.BTN_GOTO_SUBREDDIT:
            goto_subreddit_action=listbox_selected_item.getProperty('goto_subreddit_action')
            self.busy_execute_sleep(goto_subreddit_action)
            
        elif controlID == self.BTN_ZOOM_N_SLIDE:
            action=listbox_selected_item.getProperty('zoom_n_slide_action')
            self.busy_execute_sleep(action, 50,False)
            pass

        elif controlID == self.BTN_PLAY_ALL:
            #action='RunAddon(script.reddit.reader,mode=autoPlay&url=%s&name=&type=)' % self.reddit_query_of_this_gui
            #build_script( mode, url, name="", type="", script_to_call=addonID)
            action=build_script('autoPlay', self.reddit_query_of_this_gui,'','')
            #log('  PLAY_ALL '+ action)
            self.busy_execute_sleep(action, 10000,False)
            pass

        elif controlID == self.BTN_PLAY_FROM_HERE:
            #get the post_id before the selected item. (not the selected items post_id)
            i  =self.gui_listbox.getSelectedPosition()
            list_item_bs = self.gui_listbox.getListItem(i-1)
            post_id_bs   = list_item_bs.getProperty('post_id')
            
            #replace or put &after=post_id to the reddit query so that the returned posts will be "&after=post_id"
            rq=self.reddit_query_of_this_gui.split('&after=')[0]
            #log('  rq= %s ' %( rq ) )
            if post_id_bs:
                rq = rq + '&after=' + post_id_bs
            #log('  rq= %s ' %( rq ) )
            
            action=build_script('autoPlay', rq,'','')
            log('  PLAY_FROM_HERE %d %s %s' %( i, post_id_bs, list_item_bs.getLabel() ) )
            
            self.busy_execute_sleep(action, 10000,False)
            
            pass


        elif controlID == self.BTN_SLIDESHOW:
            #action='RunAddon(script.reddit.reader,mode=autoPlay&url=%s&name=&type=)' % self.reddit_query_of_this_gui
            #build_script( mode, url, name="", type="", script_to_call=addonID)
            action=build_script('autoSlideshow', self.reddit_query_of_this_gui,'','')
            log('  SLIDESHOW '+ action)
            self.busy_execute_sleep(action, 1000,False)
            pass
            
class commentsGUI(cGUI):
    
    BTN_LINKS=6771
    links_on_top=False
    links_top_selected_position=0
    listbox_selected_position=0

    #NOTE: i cannot get the links button to hide. so instead, I set a property when calling this class and have the button xml check for this property.
    #self.btn_links = self.getControl(self.BTN_LINKS)
    #self.btn_links.setVisible(True)
    def onInit(self):
        cGUI.onInit(self)
        
        #after playing a video, onInit is called again. we return the list to the state where it was at.
        if self.links_on_top:
            self.sort_links_top()
            if self.gui_listbox_SelectedPosition > 0:
                self.gui_listbox.selectItem( self.gui_listbox_SelectedPosition )
            self.setFocus(self.gui_listbox)
        #else:
        #    self.sort_links_normal()
        
        
    
    def onAction(self, action):
        #self.btn_links.setVisible(True)
        focused_control=self.getFocusId()
        if action in [ xbmcgui.ACTION_MOVE_LEFT ]:
            if focused_control==self.main_control_id: 
                self.gui_listbox_SelectedPosition  = self.gui_listbox.getSelectedPosition()
                item = self.gui_listbox.getSelectedItem()
                self.setFocusId(self.BTN_LINKS)
            elif focused_control==self.BTN_LINKS:
                self.close()
                
        if action in [ xbmcgui.ACTION_MOVE_RIGHT ]:
            if focused_control==self.BTN_LINKS:
                self.setFocusId(self.main_control_id)
                
        if action in [ xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK ]:
            self.close()

    pass

    def onClick(self, controlID):
        cGUI.onClick(self, controlID)

        if controlID == self.BTN_LINKS:
            self.toggle_links_sorting()
            #set focus back to list so that user don't have to go back
            self.setFocusId(self.main_control_id)    
            
    def getKey(self, li):
        #for sorting the comments list with links on top
        if li.getProperty('onClick_action'): return 1
        else:                                return 2

    def toggle_links_sorting(self):
        if self.links_on_top:
            self.sort_links_normal()
        else:
            self.sort_links_top()
        
            
    def sort_links_top(self):
        self.listbox_selected_position=self.gui_listbox.getSelectedPosition()

        self.gui_listbox.reset()
        self.gui_listbox.addItems( sorted( self.listing, key=self.getKey)  )
        self.gui_listbox.selectItem( self.links_top_selected_position )
        self.links_on_top=True
    
    def sort_links_normal(self):
        self.links_top_selected_position=self.gui_listbox.getSelectedPosition()
        self.gui_listbox.reset()
        self.gui_listbox.addItems( self.listing  )
        self.gui_listbox.selectItem( self.listbox_selected_position )
        self.links_on_top=False

class qGUI(xbmcgui.WindowXMLDialog):
    #called by viewImage
    
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




