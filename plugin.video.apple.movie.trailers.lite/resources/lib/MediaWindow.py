import sys
import os

import xbmc
import xbmcgui
import xbmcplugin


class _ButtonIndexError:
    pass


class DirectoryItem:
    def __init__( self, *args, **kwargs ):
        self.url = ""
        self.listitem = ""
        self.context = []
        self.isFolder = False
        self.totalItems = 0

    def addContextMenuItem( self, label, action ):
        # add menu item to our list
        self.context += [ ( label, action, ) ]


class MediaWindow:
    """ Media window class utilities """
    # constants
    BUTTON_MIN = 1
    BUTTON_MAX = 10
    
    def __init__( self, hId, wId=None, category=None, content=None, sortmethods=None, fanart=None, buttons=None ):
        # set our handle id
        self.m_handle = hId
        # set our window buttons
        self.buttons = buttons
        # get the current window if no window id supplied
        if ( wId is None ):
            self.m_window = xbmcgui.Window( xbmcgui.getCurrentWindowId() )
        else:
            self.m_window = xbmcgui.Window( wId )
        # reset button counter
        self.m_buttonId = 0
        # set plugin category
        self._set_plugin_category( category )
        # set plugin content
        self._set_media_content( content )
        # set plugin sortmethods
        self._set_sort_methods( sortmethods )
        # set fanart
        self._set_fanart( fanart )

    def _set_plugin_category( self, category ):
        # if user passed plugin content
        if ( category is not None ):
            # set plugin category
            xbmcplugin.setPluginCategory( handle=self.m_handle, category=category )

    def _set_media_content( self, content ):
        # if user passed plugin content
        if ( content is not None ):
            # set media content
            xbmcplugin.setContent( handle=self.m_handle, content=content )

    def _set_sort_methods( self, sortmethods ):
        # if there are sortmethods add them
        if ( sortmethods is not None ):
            # enumerate thru and add each sort method
            for sortmethod in sortmethods:
                xbmcplugin.addSortMethod( handle=self.m_handle, sortMethod=sortmethod )

    def _set_fanart( self, fanart ):
        # if user passed fanart tuple (path, method,)
        if ( fanart is not None ):
            # if skin has fanart image use it
            fanart_image = os.path.join( sys.modules[ "__main__" ].__plugin__, fanart[ 1 ] + "-fanart.png" )
            if ( xbmc.skinHasImage( fanart_image ) ):
                xbmcplugin.setPluginFanart( handle=self.m_handle, image=fanart_image )
            # set our fanart from user setting
            elif ( fanart[ 0 ] ):
                xbmcplugin.setPluginFanart( handle=self.m_handle, image=fanart[ 0 ] )

    def add( self, item ):
        # add context menu items to listitem with replaceItems = True so only ours show
        if ( item.context ):
            item.listitem.addContextMenuItems( item.context, replaceItems=True )
        # add directory item
        return xbmcplugin.addDirectoryItem( handle=self.m_handle, url=item.url, listitem=item.listitem, isFolder=item.isFolder, totalItems=item.totalItems )

    def end( self, succeeded=True ):
        # send notification we're finished, successfully or unsuccessfully
        xbmcplugin.endOfDirectory( handle=self.m_handle, succeeded=succeeded )
        # set window buttons
        self._set_buttons( succeeded )

    def _set_buttons( self, ok=True ):
        # only set buttons on a successful directory listing
        if ( ok and self.buttons is not None ):
            # clear all buttons
            self._clear_buttons()
            # set buttons heading
            self.m_window.setProperty( "PluginButtons.Heading", self.buttons[ 0 ] )
            # enumerate thru and set each button
            for label, onclick, onfocus, onunfocus, bId in self.buttons[ 1 ]:
                # set button
                self._set_button( label, onclick, onfocus, onunfocus, bId )

    def _set_button( self, label, onclick=None, onfocus=None, onunfocus=None, bId=None ):
        # increment bId if none supplied
        if ( bId is None ):
            bId = self.m_buttonId + 1
        # if it's not a valid button id raise button error
        if ( not ( self.BUTTON_MIN <= bId <= self.BUTTON_MAX ) ):
            raise _ButtonIndexError
        # set the counter
        self.m_buttonId = bId
        # set button label property
        self.m_window.setProperty( "PluginButton.%d.Label" % bId, label )
        # set optional button properties
        if ( onclick is not None ):
            self.m_window.setProperty( "PluginButton.%d.OnClick" % bId, onclick )
        if ( onfocus is not None ):
            self.m_window.setProperty( "PluginButton.%d.OnFocus" % bId, onfocus )
        if ( onunfocus is not None ):
            self.m_window.setProperty( "PluginButton.%d.OnUnFocus" % bId, onunfocus )

    def _clear_buttons( self ):
        # we want to clear all buttons in case another script uses them
        for bId in range( self.BUTTON_MIN, self.BUTTON_MAX ):
            self.m_window.clearProperty( "PluginButton.%d.Label" % bId )
            self.m_window.clearProperty( "PluginButton.%d.OnClick" % bId )
            self.m_window.clearProperty( "PluginButton.%d.OnFocus" % bId )
            self.m_window.clearProperty( "PluginButton.%d.OnUnFocus" % bId )
