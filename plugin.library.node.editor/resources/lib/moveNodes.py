# coding=utf-8
import sys
import xbmc, xbmcaddon, xbmcgui

from resources.lib.common import *


def getNewOrder( currentPositions, indexToMove ):
    # Show select dialog
    w = ShowDialog( "DialogSelect.xml", CWD, order=currentPositions, focus=indexToMove, windowtitle=LANGUAGE(30104) )
    w.doModal()
    newOrder = w.newOrder
    del w

    return newOrder

class ShowDialog( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.order = kwargs.get( "order" )
        self.windowtitle = kwargs.get( "windowtitle" )
        self.selectedItem = kwargs.get( "focus" )
        self.newOrder = []

    def onInit(self):
        self.list = self.getControl(3)

        # Set visibility
        self.getControl(3).setVisible(True)
        self.getControl(3).setEnabled(True)
        self.getControl(5).setVisible(False)
        self.getControl(6).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)

        # Set Cancel label
        self.getControl(7).setLabel(xbmc.getLocalizedString(222))

        # Add all the items to the list
        for i, key in enumerate( sorted( self.order ) ):
            # Get the label and localise if necessary
            label = self.order[ key ][ 0 ]
            if label.isdigit():
                label = xbmc.getLocalizedString( int( label ) )
                if label == "":
                    label = self.order[ key ][ 0 ]
            if self.order[ key ][ 3 ] == "folder":
                label = "%s >" %( label )

            # Create the listitem and add it
            listitem = xbmcgui.ListItem( label=label )
            self.list.addItem( listitem )

            # And add it to the list that we'll eventually return
            self.newOrder.append( self.order[ key ] )

            # If it's the item we're moving, save it separately
            if i == self.selectedItem:
                self.itemMoving = self.order[ key ]

        # Set focus
        self.list.selectItem(self.selectedItem)
        self.setFocus(self.list)

    def onAction(self, action):
        # Check if the selected item has changed
        if self.list.getSelectedPosition() != self.selectedItem:
            # Remove the item we're moving from the list of items
            self.newOrder.pop( self.selectedItem )

            # Add the item we're moving at its new location
            self.newOrder.insert( self.list.getSelectedPosition(), self.itemMoving )

            # Update its current current position
            self.selectedItem = self.list.getSelectedPosition()

            # Update the labels of all list items
            for i in range( len( self.newOrder ) ):
                item = self.list.getListItem( i )
                label = self.newOrder[ i ][ 0 ]
                if label.isdigit():
                    label = xbmc.getLocalizedString( int( label ) )
                    if label == "":
                        label = self.newOrder[ i ][ 0 ]
                if self.newOrder[ i ][ 3 ] == "folder":
                    label = "%s >" %( label )
                if item.getLabel() != label:
                    item.setLabel( label )

        if action.getId() in ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.close()
            return

    def onClick(self, controlID):
        if controlID == 7:
            # Cancel button
            self.newOrder = None
        
        self.close()
