#
#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import os, xbmc, xbmcgui

class LogViewer( xbmcgui.WindowXMLDialog ):
    ACTION_EXIT_SCRIPT = ( 9, 10, )
    LIST_CONTROL_ID    = 30010

    def __init__( self, *args, **kwargs ):
        print 'LogViewer()'
        xbmcgui.WindowXML.__init__( self )
        self.txtlines = kwargs[ 'stack' ]

    def onInit( self ):
        self.txtbox = self.getControl( 5 )
        self.txtlines[0] = '.'+' '*5+self.txtlines[0]
        txt = '\n.     '.join(self.txtlines)
        self.txtbox.setText( txt )

    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
        if ( action in self.ACTION_EXIT_SCRIPT ):
            self.close()

    def onClick( self, controlId ):
        pass
                 
