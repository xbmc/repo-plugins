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

import xbmcgui
import MypicsDB as MPDB
import common


STATUS_LABEL       = 100
CHECKED_LABEL      = 101
BUTTON_OK          = 102
BUTTON_CANCEL      = 103
BUTTON_MATCHALL    = 104
TAGS_COLUMN        = 105
CONTENT_COLUMN     = 106

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
        
    def setDelegate(self, filterfunc):
        self.filter = filterfunc
        
    def onInit( self ):  
        self.setup_all()

    def setup_all( self ):
        self.getControl( STATUS_LABEL ).setLabel( common.getstring(30610) )
        self.getControl( TAGS_COLUMN ).setLabel(  common.getstring(30601) )        
        self.getControl( CONTENT_COLUMN ).setLabel( common.getstring(30602) )        
        self.getControl( BUTTON_OK ).setLabel( common.getstring(30613) )
        self.getControl( BUTTON_CANCEL ).setLabel( common.getstring(30614) )
        self.getControl( BUTTON_MATCHALL ).setLabel( common.getstring(30615) )
        self.getControl( TAGS_LIST ).reset()

        
        self.TagTypes = [u"%s"%k  for k in MPDB.list_TagTypes()]
        self.CurrentlySelectedTagType = ''
        self.checkedTags = 0
        self.bAnd = False
        self.CheckTagNames = {}
        
        if self.checkedTags == 1:
            self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30611) )
        else:
            self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30612)% (self.checkedTags) )
        

        i = 0
        for TagType in self.TagTypes:
            TagTypeItem = xbmcgui.ListItem( label=TagType)   
            TagTypeItem.setProperty( "checked", "transparent.png")
            self.getControl( TAGS_LIST ).addItem( TagTypeItem )

            if i == 0:
                self.loadTagContentList(TagType)
                i=1;

            self.setFocus( self.getControl( TAGS_LIST ) )
            self.getControl( TAGS_LIST ).selectItem( 0 )
            self.getControl( TAGS_CONTENT_LIST ).selectItem( 0 )

     
    def isContentChecked(self, tagType, tagContent):
        key = common.smart_unicode(tagType) + '||' + common.smart_unicode(tagContent)
        if key in self.CheckTagNames :
            checked = self.CheckTagNames[ key ]    
        else :
            self.CheckTagNames[ key ] = 0
            checked = 0    
        return checked
    
    def loadTagContentList(self, tagType) :
    
        self.getControl( TAGS_CONTENT_LIST ).reset()
        TagContents = [u"%s"%k  for k in MPDB.list_Tags(tagType)]

        self.CurrentlySelectedTagType = tagType
        
        for TagContent in TagContents:
                
            TagContentItem = xbmcgui.ListItem( label=tagType, label2=TagContent) 
            TagContentItem.setProperty( "summary", TagContent )    
            
            if self.isContentChecked(tagType, TagContent) == 0:
                TagContentItem.setProperty( "checked", "transparent.png")
            else:
                TagContentItem.setProperty( "checked", "checkbutton.png")
            
            self.getControl( TAGS_CONTENT_LIST ).addItem( TagContentItem )
            
    def onClick( self, controlId ):
        pass    

    def onFocus( self, controlId ):
        self.controlId = controlId

    def checkGUITagContent(self, item, checked):
        
        AlreadyChecked = item.getProperty("checked")
 
        if checked == -1:
            item.setProperty( "checked", "uncheckbutton.png")
        elif checked == 0:
            item.setProperty( "checked", "transparent.png")
            if AlreadyChecked != "transparent.png":
                self.checkedTags -= 1

        else:
            item.setProperty( "checked", "checkbutton.png")
            if AlreadyChecked == "transparent.png":
                self.checkedTags += 1

        self.getControl( TAGS_CONTENT_LIST ).setVisible(False)
        self.getControl( TAGS_CONTENT_LIST ).setVisible(True)    

    def onAction( self, action ):
        #try:
            # Cancel
            if ( action.getId() in CANCEL_DIALOG or self.getFocusId() == BUTTON_CANCEL and action.getId() in SELECT_ITEM ):
                arraytrue = []
                arrayfalse = []
                self.filter (arraytrue,arrayfalse,False)
                self.close()
                
            # Okay
            if ( self.getFocusId() == BUTTON_OK and action.getId() in SELECT_ITEM ):
                arraytrue = []
                arrayfalse = []
                
                for key, value in self.CheckTagNames.iteritems():
                    if value == 1:
                        arraytrue.append( key)
 
                    if value == -1:
                        arrayfalse.append( key)
                
                self.filter (arraytrue, arrayfalse, self.bAnd )
                self.close()
            
            # Match all button
            if ( action.getId() in SELECT_ITEM and self.getFocusId() == BUTTON_MATCHALL ):
                self.bAnd = not self.bAnd
            
            # Select or deselect item in TagTypes list
            if ( action.getId() in SELECT_ITEM and self.getFocusId() == TAGS_LIST ):
                item = self.getControl( TAGS_LIST ).getSelectedItem()
                pos  = self.getControl( TAGS_LIST ).getSelectedPosition()
                if self.CurrentlySelectedTagType != self.TagTypes[pos]:
                    self.loadTagContentList(self.TagTypes[pos])
            
            # Select or deselect item in TagContents list
            if ( action.getId() in SELECT_ITEM and self.getFocusId() == TAGS_CONTENT_LIST ):
                item = self.getControl( TAGS_CONTENT_LIST ).getSelectedItem()
                pos  = self.getControl( TAGS_CONTENT_LIST ).getSelectedPosition()
                if pos != -1 and item != None:
                    checked = item.getProperty("checked")
                    key = common.smart_unicode(self.CurrentlySelectedTagType) + '||' + common.smart_unicode(item.getLabel2())
                    
                    if checked == "checkbutton.png":
                        self.checkGUITagContent(item, -1)
                        self.CheckTagNames[ key ] = -1
                    elif checked == "uncheckbutton.png":
                        self.checkGUITagContent(item, 0)
                        self.CheckTagNames[ key ] = 0
                    else :
                        self.checkGUITagContent(item, 1)
                        self.CheckTagNames[ key ] = 1
                        
                    

                    if self.checkedTags == 1:
                        self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30611) )
                    else:
                        self.getControl( CHECKED_LABEL ).setLabel(  common.getstring(30612)% (self.checkedTags) )
                    self.getControl( CHECKED_LABEL ).setVisible(False)
                    self.getControl( CHECKED_LABEL ).setVisible(True)





