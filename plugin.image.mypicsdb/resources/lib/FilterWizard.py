#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
import xbmc
import xbmcgui
import urllib
import MypicsDB as MPDB
import CharsetDecoder as decoder

_ = sys.modules[ "__main__" ].__language__


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
    
    def __init__( self, xml, cwd, default, filter):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.filter = filter
    
    def onInit( self ):  
        self.setup_all()

    def setup_all( self ):
        self.getControl( STATUS_LABEL ).setLabel( _(30610) )
        self.getControl( TAGS_COLUMN ).setLabel(  _(30601) )        
        self.getControl( CONTENT_COLUMN ).setLabel( _(30602) )        
        self.getControl( BUTTON_OK ).setLabel( _(30613) )
        self.getControl( BUTTON_CANCEL ).setLabel( _(30614) )
        self.getControl( BUTTON_MATCHALL ).setLabel( _(30615) )
        self.getControl( TAGS_LIST ).reset()

        
        self.TagTypes = [u"%s"%k  for k in MPDB.list_TagTypes()]
        self.CurrentlySelectedTagType = ''
        self.checkedTags = 0
        self.bAnd = False
        self.CheckTagNames = {}
        
        if self.checkedTags == 1:
            self.getControl( CHECKED_LABEL ).setLabel(  _(30611) )
        else:
            self.getControl( CHECKED_LABEL ).setLabel(  _(30612)% (self.checkedTags) )
        
        
        TotalTagTypes = len(self.TagTypes)
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
        key = decoder.smart_unicode(tagType) + '||' + decoder.smart_unicode(tagContent)
        if key in self.CheckTagNames :
            checked = self.CheckTagNames[ key ]    
        else :
            self.CheckTagNames[ key ] = 0
            checked = 0    
        return checked
    
    def loadTagContentList(self, tagType) :
    
        self.getControl( TAGS_CONTENT_LIST ).reset()
        TagContents = [u"%s"%k  for k in MPDB.list_Tags(tagType)]
        TotalTagContents = len(TagContents)
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
 
        if checked == 0:
            item.setProperty( "checked", "transparent.png")
            if AlreadyChecked != "transparent.png":
                self.checkedTags -= 1

        else:
            item.setProperty( "checked", "checkbutton.png")
            if AlreadyChecked != "checkbutton.png":
                self.checkedTags += 1

        self.getControl( TAGS_CONTENT_LIST ).setVisible(False)
        self.getControl( TAGS_CONTENT_LIST ).setVisible(True)    

    def onAction( self, action ):
        #try:
            # Cancel
            if ( action.getId() in CANCEL_DIALOG or self.getFocusId() == BUTTON_CANCEL and action.getId() in SELECT_ITEM ):
                array = []
                self.filter (array, False)
                self.close()
                
            # Okay
            if ( self.getFocusId() == BUTTON_OK and action.getId() in SELECT_ITEM ):
                returnArray = []
                for key, value in self.CheckTagNames.iteritems():
                    if value == 1:
                        returnArray.append( key)
                self.filter (returnArray, self.bAnd )
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
                    key = decoder.smart_unicode(self.CurrentlySelectedTagType) + '||' + decoder.smart_unicode(item.getLabel2())
                    
                    if checked == "checkbutton.png":
                        self.checkGUITagContent(item, 0)
                        self.CheckTagNames[ key ] = 0
                    else :
                        self.checkGUITagContent(item, 1)
                        self.CheckTagNames[ key ] = 1
                        
                    

                    if self.checkedTags == 1:
                        self.getControl( CHECKED_LABEL ).setLabel(  _(30611) )
                    else:
                        self.getControl( CHECKED_LABEL ).setLabel(  _(30612)% (self.checkedTags) )
                    self.getControl( CHECKED_LABEL ).setVisible(False)
                    self.getControl( CHECKED_LABEL ).setVisible(True)

            #else:
            #    print "ActionID = " + str( action.getId() )
        #except:
        #    pass



