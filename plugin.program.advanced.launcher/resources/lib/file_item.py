# -*- coding: UTF-8 -*-

import os
import xbmc

THUMBS_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails" )

class Thumbnails:
    def get_cached_thumb( self, path1, path2, SPLIT=False ):
        # get the locally cached thumb
        filename = xbmc.getCacheThumbName( path1 )
        if SPLIT:
            thumb = os.path.join( filename[ 0 ], filename )
        else:
            thumb = filename
        return os.path.join( path2, thumb )

    def get_cached_covers_thumb( self, strPath ):
        return self.get_cached_thumb( strPath, THUMBS_CACHE_PATH, True )

