from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcplugin
from kodi_six.utils import py2_decode
import os, sys
try:
    from urllib.parse import unquote_plus as _unquote_plus
except ImportError:
    from urllib import unquote_plus as _unquote_plus

addon        = xbmcaddon.Addon()
addonname    = addon.getAddonInfo('id')
addonversion = addon.getAddonInfo('version')
addonpath    = addon.getAddonInfo('path')
addonicon    = xbmc.translatePath('%s/icon.png' % addonpath )
language     = addon.getLocalizedString
preamble     = '[Where Are You]'



class Main:

    def __init__( self ):
        self._parse_argv()
        if self.TITLE and self.MESSAGE:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok( self.TITLE, self.MESSAGE )
            self.play_video( os.path.join( addonpath, 'resources', 'blank.mp4' ) )
        else:
            xbmc.log( '%s One or both of title ("%s") and message ("%s") not set.' % (preamble, self.TITLE, self.MESSAGE), xbmc.LOGWARNING )


    def _parse_argv( self ):
        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[2].split( "&" ) )
        except IndexError:
            params = {}        
        except Exception as e:
            xbmc.log( '%s unexpected error while parsing arguments %s' % (preamble, e), xbmc.LOGWARNING )
            params = {}
        self.TITLE = py2_decode( _unquote_plus( params.get( 'title', '') ) )
        self.MESSAGE = py2_decode( _unquote_plus( params.get( 'message', '') ) )


    def play_video( self, path ):
        play_item = xbmcgui.ListItem( path=path )
        try:
            xbmcplugin.setResolvedUrl( int( sys.argv[1] ), True, listitem=play_item )
        except IndexError:
            return
