#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import xbmc, xbmcgui
from time import strftime,strptime
import datetime
import MypicsDB as MPDB
import common


STATUS_LABEL       = 100
CHECKED_LABEL      = 101
#FILTER_LABEL       = 110
BUTTON_OK          = 102
BUTTON_CANCEL      = 103
BUTTON_MATCHALL    = 104
TAGS_COLUMN        = 105
CONTENT_COLUMN     = 106
LOAD_FILTER        = 107
SAVE_FILTER        = 108
CLEAR_FILTER       = 109
DELETE_FILTER      = 111
BUTTON_DATE        = 112
FILTER_NAME        = 113
TAGS_LIST          = 120
TAGS_CONTENT_LIST  = 122

CANCEL_DIALOG      = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_SELECT_ITEM = 7
ACTION_MOUSE_START = 100
ACTION_TAB         = 18
SELECT_ITEM = (ACTION_SELECT_ITEM, ACTION_MOUSE_START)


class FilterWizard( xbmcgui.WindowXMLDialog ):
    
    def __init__( self, xml, cwd, default):
        xbmcgui.WindowXMLDialog.__init__(self)


    def onInit( self ):  
        self.setup_all('')

 
    def onAction( self, action ):
        # Cancel
        if ( action.getId() in CANCEL_DIALOG or self.getFocusId() == BUTTON_CANCEL and action.getId() in SELECT_ITEM ):
            arraytrue = []
            arrayfalse = []
            self.filter (arraytrue,arrayfalse,False,'','')
            self.close()

        # Okay
        elif ( self.getFocusId() == BUTTON_OK and action.getId() in SELECT_ITEM ):
            arraytrue = []
            arrayfalse = []

            for key, value in self.active_tags.iteritems():
                if value == 1:
                    arraytrue.append( key)

                if value == -1:
                    arrayfalse.append( key)

            self.filter (arraytrue, arrayfalse, self.use_and, self.start_date, self.end_date )

            self.getControl( BUTTON_OK ).setEnabled(False)
            self.getControl( BUTTON_CANCEL ).setEnabled(False)
            self.getControl( BUTTON_MATCHALL ).setEnabled(False)
            self.getControl( LOAD_FILTER ).setEnabled(False)
            self.getControl( SAVE_FILTER ).setEnabled(False)
            self.getControl( CLEAR_FILTER ).setEnabled(False)
            self.getControl( DELETE_FILTER ).setEnabled(False)
            self.getControl( TAGS_LIST ).setEnabled(False)
            self.getControl( TAGS_CONTENT_LIST ).setEnabled(False)

            MPDB.filterwizard_save_filter( self.last_used_filter_name, self.active_tags, self.use_and, self.start_date, self.end_date)

            self.close()

        # Match all button
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == BUTTON_MATCHALL ):
            self.use_and = not self.use_and

        # Load filter settings
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == LOAD_FILTER ):
            self.show_filter_settings()
            
        # Save filter settings
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == SAVE_FILTER ):
            self.save_filter_settings()
            
        # Clear filter settings
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == CLEAR_FILTER ):
            self.clear_settings()
            
        # Delete filter settings
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == DELETE_FILTER ):
            self.delete_filter_settings()
            
        # Set start and end date
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == BUTTON_DATE ):
            self.set_filter_date()            

            
        # Select or deselect item in TagTypes list
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == TAGS_LIST ):
            item = self.getControl( TAGS_LIST ).getSelectedItem()
            pos  = self.getControl( TAGS_LIST ).getSelectedPosition()
            if self.currently_selected_tagtypes != self.tag_types[pos]:
                self.load_tag_content_list(self.tag_types[pos])
        
        # Select or deselect item in TagContents list
        elif ( action.getId() in SELECT_ITEM and self.getFocusId() == TAGS_CONTENT_LIST ):
            # get selected item
            item = self.getControl( TAGS_CONTENT_LIST ).getSelectedItem()
            pos  = self.getControl( TAGS_CONTENT_LIST ).getSelectedPosition()
            if pos != -1 and item != None:            
            
                checked = item.getProperty("checked")
                key = common.smart_unicode(self.currently_selected_tagtypes) + '||' + common.smart_unicode(item.getLabel2())
                
                if checked == "checkbutton.png":
                    self.check_gui_tag_content(item, -1)
                    self.active_tags[ key ] = -1
                elif checked == "uncheckbutton.png":
                    self.check_gui_tag_content(item, 0)
                    self.active_tags[ key ] = 0
                else :
                    self.check_gui_tag_content(item, 1)
                    self.active_tags[ key ] = 1
                    
                

                if self.checked_tags == 1:
                    self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30611) )
                else:
                    self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30612)% (self.checked_tags) )
                self.getControl( CHECKED_LABEL ).setVisible(False)
                self.getControl( CHECKED_LABEL ).setVisible(True)


    def set_delegate(self, filterfunc):
        self.filter = filterfunc


    def check_gui_tag_content(self, item, checked):

        AlreadyChecked = item.getProperty("checked")
 
        if checked == -1:
            item.setProperty( "checked", "uncheckbutton.png")
        elif checked == 0:
            item.setProperty( "checked", "transparent.png")
            if AlreadyChecked != "transparent.png":
                self.checked_tags -= 1

        else:
            item.setProperty( "checked", "checkbutton.png")
            if AlreadyChecked == "transparent.png":
                self.checked_tags += 1

        self.getControl( TAGS_CONTENT_LIST ).setVisible(False)
        self.getControl( TAGS_CONTENT_LIST ).setVisible(True)    


    def setup_all( self, filtersettings = ""):
        self.getControl( STATUS_LABEL ).setLabel( common.getstring(30610) )
        #self.getControl( FILTER_LABEL ).setLabel( common.getstring(30652) )
        self.getControl( TAGS_COLUMN ).setLabel(  common.getstring(30601) )        
        self.getControl( CONTENT_COLUMN ).setLabel( common.getstring(30602) )        
        self.getControl( BUTTON_OK ).setLabel( common.getstring(30613) )
        self.getControl( BUTTON_CANCEL ).setLabel( common.getstring(30614) )
        self.getControl( BUTTON_MATCHALL ).setLabel( common.getstring(30615) )
        self.getControl( LOAD_FILTER ).setLabel( common.getstring(30616) )
        self.getControl( SAVE_FILTER ).setLabel( common.getstring(30617) )
        self.getControl( CLEAR_FILTER ).setLabel( common.getstring(30618) )
        self.getControl( DELETE_FILTER ).setLabel( common.getstring(30619) )
        self.getControl( BUTTON_DATE ).setLabel( common.getstring(30164) )
        if filtersettings != '':
            self.getControl( FILTER_NAME ).setLabel( common.getstring(30652) +' '+filtersettings)
        else:
            self.getControl( FILTER_NAME ).setLabel( '' )
        
        self.getControl( TAGS_LIST ).reset()

        self.tag_types = [u"%s"%k  for k in MPDB.list_TagTypes()]
        self.currently_selected_tagtypes = ''
        self.checked_tags = 0
        self.use_and = False
        self.start_date = ''
        self.end_date   = ''
        self.active_tags = {}
        self.last_used_filter_name = "  " + common.getstring(30607)

        self.getControl( TAGS_CONTENT_LIST ).reset()
        self.getControl( TAGS_LIST ).reset()
        
        # load last filter settings
        if filtersettings != "":
            self.active_tags, self.use_and, self.start_date, self.end_date = MPDB.filterwizard_load_filter(filtersettings)
            if self.use_and:
                self.getControl( BUTTON_MATCHALL ).setSelected(1)
            if self.start_date != "" or self.end_date != "":
                self.getControl( BUTTON_DATE ).setLabel( self.start_date + ' ... ' + self.end_date )
            else:
                self.getControl( BUTTON_DATE ).setLabel( common.getstring(30164) )
            self.getControl( BUTTON_DATE ).setVisible(False)
            self.getControl( BUTTON_DATE ).setVisible(True)                   
        
        for key in self.active_tags:
            if self.active_tags[key] != 0:
                self.checked_tags += 1

        if self.checked_tags == 1:
            self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30611) )
        else:
            self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30612)% (self.checked_tags) )

        self.init_tags()     

    def init_tags(self):
        i = 0
        for TagType in self.tag_types:
            TagTypeItem = xbmcgui.ListItem( label=TagType)   
            TagTypeItem.setProperty( "checked", "transparent.png")
            self.getControl( TAGS_LIST ).addItem( TagTypeItem )

            if i == 0:
                self.load_tag_content_list(TagType)
                i=1;

            self.setFocus( self.getControl( TAGS_LIST ) )
            self.getControl( TAGS_LIST ).selectItem( 0 )
            self.getControl( TAGS_CONTENT_LIST ).selectItem( 0 )


    def is_content_checked(self, tagType, tagContent):
        key = common.smart_unicode(tagType) + '||' + common.smart_unicode(tagContent)
        if key in self.active_tags :
            checked = self.active_tags[ key ]    
        else :
            self.active_tags[ key ] = 0
            checked = 0    
        return checked

        
    def show_filter_settings(self):
        filters = MPDB.filterwizard_list_filters()
        dialog = xbmcgui.Dialog()
        ret = dialog.select(common.getstring(30608), filters)
        if ret > -1:
            self.setup_all(filters[ret])


    def load_tag_content_list(self, tagType) :
    
        self.getControl( TAGS_CONTENT_LIST ).reset()
        TagContents = [u"%s"%k  for k in MPDB.list_tags(tagType)]

        self.currently_selected_tagtypes = tagType
        
        for TagContent in TagContents:
                
            TagContentItem = xbmcgui.ListItem( label=tagType, label2=TagContent) 
            TagContentItem.setProperty( "summary", TagContent )    
            
            if self.is_content_checked(tagType, TagContent) == 0:
                TagContentItem.setProperty( "checked", "transparent.png")
            elif self.is_content_checked(tagType, TagContent) == 1:
                TagContentItem.setProperty( "checked", "checkbutton.png")
            else:
                TagContentItem.setProperty( "checked", "uncheckbutton.png")
                
            self.getControl( TAGS_CONTENT_LIST ).addItem( TagContentItem )


    def clear_settings(self):
        self.active_tags.clear()
        self.checked_tags = 0
        self.use_and = False
        self.getControl( BUTTON_MATCHALL ).setSelected(0)

        self.load_tag_content_list(self.tag_types[0])
        
        self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30612)% (self.checked_tags) )
        self.getControl( CHECKED_LABEL ).setVisible(False)
        self.getControl( CHECKED_LABEL ).setVisible(True)
        
        self.getControl( BUTTON_DATE ).setLabel( common.getstring(30164) )
        self.getControl( BUTTON_DATE ).setVisible(False)
        self.getControl( BUTTON_DATE ).setVisible(True)   

        self.getControl( FILTER_NAME ).setLabel( '' )
        self.getControl( FILTER_NAME ).setVisible(False)
        self.getControl( FILTER_NAME ).setVisible(True)   

    def delete_filter_settings(self):
        filters = MPDB.filterwizard_list_filters()
        # don't delete the last used filter
        filters.remove(self.last_used_filter_name)
        dialog = xbmcgui.Dialog()
        ret = dialog.select(common.getstring(30608), filters)
        if ret > -1:
            MPDB.filterwizard_delete_filter(filters[ret])


    def save_filter_settings(self):
        # Display a list of already saved filters to give the possibility to override a filter
        filters = []
        filters.append( common.getstring(30653) )
        filters = filters + MPDB.filterwizard_list_filters()
        filters.remove(self.last_used_filter_name)
        dialog = xbmcgui.Dialog()
        ret = dialog.select(common.getstring(30608), filters)
        if ret > 0:
            MPDB.filterwizard_save_filter(filters[ret], self.active_tags, self.use_and, self.start_date, self.end_date)
        if ret == 0:
            kb = xbmc.Keyboard()
            kb.setHeading(common.getstring(30609))
            kb.doModal()
            filtersettings = ""
            if (kb.isConfirmed()):
                filtersettings = kb.getText()
                MPDB.filterwizard_save_filter(filtersettings, self.active_tags, self.use_and, self.start_date, self.end_date)

                if filtersettings != '':
                    self.getControl( FILTER_NAME ).setLabel( common.getstring(30652) +' '+filtersettings)
                else:
                    self.getControl( FILTER_NAME ).setLabel( '' )
        self.getControl( FILTER_NAME ).setVisible(False)
        self.getControl( FILTER_NAME ).setVisible(True)   
        
    def set_filter_date(self):
    
        dialog = xbmcgui.Dialog()
        if self.start_date == '':
            self.start_date = str(datetime.datetime.now())[:10]
        if self.end_date == '':
            self.end_date = str(datetime.datetime.now())[:10]

        try:
            d = dialog.numeric(1, common.getstring(30117) ,strftime("%d/%m/%Y",strptime(self.start_date,"%Y-%m-%d")) )
            if d != '':    
                self.start_date = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))
            else:
                self.start_date =''
            common.log('', str(self.start_date))
            
            d = dialog.numeric(1, common.getstring(30118) ,strftime("%d/%m/%Y",strptime(self.end_date,"%Y-%m-%d")) )
            if d != '':
                self.end_date = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))
            else:
                self.end_date =''
            common.log('', str(self.end_date))
        except:
            pass

        if self.start_date != '' or self.end_date != '':
            self.getControl( BUTTON_DATE ).setLabel( self.start_date + ' ... ' + self.end_date )
        else:
            self.getControl( BUTTON_DATE ).setLabel( common.getstring(30164) )
        self.getControl( BUTTON_DATE ).setVisible(False)
        self.getControl( BUTTON_DATE ).setVisible(True)        