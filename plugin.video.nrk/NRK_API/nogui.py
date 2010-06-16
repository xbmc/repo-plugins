import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import urllib
from utils import Key

pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__ )
__settings__ = sys.modules[ "__main__" ].__settings__

class Main:
    
    def __init__(self):
    
        self.key = Key( sys.argv[2] )
        #self.settings = {}
        
        if self.key.action == 'download':
            self.download()
            
            
    def download( self ):
    
        download_path = __settings__.getSetting("download_path")
        
                
        url = self.key.url 
        tmp_path = xbmc.translatePath( "special://temp/%s" % ( os.path.basename( url ), ) )
        tmp_path = xbmc.makeLegalFilename(tmp_path)
        filename = self.key.name
        filepath = xbmc.makeLegalFilename( os.path.join( xbmc.translatePath( download_path ), filename ) )
        self.filepath = filepath
        print filepath
        print tmp_path
        
        #if ( not os.path.isfile( self.filepath.encode( "utf-8" ) ) ):
        #    if ( not os.path.isfile( tmp_path.encode( "utf-8" ) ) ):
        response = urllib.urlretrieve( self.key.url, tmp_path, self._report_hook )
        print response        
        ok = self._finalize_download( tmp_path )
        if ( not ok ): 
            raise Exception
        """except:
            print 'Error downloading file!'
            urllib.urlcleanup()
            remove_tries = 3
            while remove_tries and os.path.isfile( tmp_path ):
                try:
                    os.remove( tmp_path )
                except:
                    remove_tries -= 1
                    xbmc.sleep( 1000 )
            pDialog.close()
            self.filepath = """


    def _report_hook( self, count, blocksize, totalsize ):
        percent = int( float( count * blocksize * 100) / totalsize )
        msg1 = '%s' % os.path.split( self.filepath )[ 1 ]
        msg2 = '%s' % os.path.split( self.filepath )[ 0 ]
        pDialog.update( percent, msg1, msg2 )
        if ( pDialog.iscanceled() ): raise
        
    
    def _finalize_download( self, tmp_path ):
        #try:
        if ( tmp_path != self.filepath ):
            msg1 = '%s' % ( os.path.split( self.filepath )[ 1 ], )
            msg2 = '%s' % ( os.path.split( self.filepath )[ 0 ], )
            pDialog.update( -1, msg1, msg2 )                
            xbmc.sleep( 50 ) # necessary for dialog to update
            xbmc.executehttpapi( "FileCopy(%s,%s)" % ( tmp_path, self.filepath.encode( "utf-8" ), ) )
            os.remove( tmp_path )
            thumbpath = os.path.splitext( self.filepath )[ 0 ] + ".tbn"
            msg1 = '%s' % ( os.path.split( thumbpath )[ 1 ], )
            pDialog.update( -1, msg1, msg2 )
            xbmc.sleep( 50 ) # necessary for dialog to update
            #xbmc.executehttpapi( "FileCopy(%s,%s)" % ( g_thumbnail, thumbpath.encode( "utf-8" ), ) )
        return True
        #except:
        #    return False

