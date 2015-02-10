
#       Copyright (C) 2013-2014
#       Sean Poyser (seanpoyser@gmail.com)
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

# This script is to allow the excellent XBMC GlobalSearch script by Ronie to be
# used without the need for manual entry via the on-screen keyboard.
# It should be called like this:
#
# xbmc.executebuiltin('RunScript('FULLPATHTOSCRIPT/globalsearch.py', searchstring:SEARCHTERM)')
#


import os, sys
import xbmc, xbmcaddon

__addon__        = xbmcaddon.Addon('script.globalsearch')
__addonid__      = __addon__.getAddonInfo('id')
__addonversion__ = __addon__.getAddonInfo('version')
__language__     = __addon__.getLocalizedString
__cwd__          = __addon__.getAddonInfo('path').decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")

sys.path.append(__resource__)

def doSearch():
    searchstring = None
    if len(sys.argv) > 1:
        try:
            param = sys.argv[1]
            if param.startswith('searchstring:'):
                import urllib
                searchstring = param.split(':', 1)[-1]
                searchstring = urllib.unquote_plus(searchstring)
                searchstring = searchstring.replace('\'', '')
                searchstring = searchstring.replace('"',  '')
        except:
            searchstring = None
            
    if not searchstring:     
        keyboard = xbmc.Keyboard( '', __language__(32101), False )
        keyboard.doModal()
        if ( keyboard.isConfirmed() ):
            searchstring = keyboard.getText()

    if searchstring:
        import gui
        ui = gui.GUI( "script-globalsearch-main.xml", __cwd__, "Default", searchstring=searchstring )
        ui.doModal()
        del ui
        sys.modules.clear()

doSearch()