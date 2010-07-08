import os
import sys
import xbmc

__plugin__ = sys.modules[ "__main__" ].__plugin__
__version__ = sys.modules[ "__main__" ].__version__
__svn_revision__ = sys.modules[ "__main__" ].__svn_revision__
__XBMC_Revision__ = sys.modules[ "__main__" ].__XBMC_Revision__


def LOG( text, level=xbmc.LOGDEBUG, heading=False ):
    # log a heading
    if ( heading ):
        xbmc.log( "-" * 70, level )
    # log message
    xbmc.log( text, level )
    # log a footer
    if ( heading ):
        xbmc.log( "-" * 70, level )

def check_compatible():
    # spam scripts statistics to log
    LOG( "=" * 70, xbmc.LOGNOTICE )
    LOG( "[PLUGIN] - %s (Version: %s-r%s) initialized!" % ( __plugin__, __version__, __svn_revision__.replace( "$", "" ).replace( "Revision", "" ).replace( ":", "" ).strip() ), xbmc.LOGNOTICE )
    LOG( "=" * 70, xbmc.LOGNOTICE )
    #return result
    return True

def get_filesystem( download_path ):
    # use win32 illegal characters for smb shares to be safe (eg run on linux, save to windows)
    if ( download_path.startswith( "smb://" ) ):
        filesystem = "win32"
    else:
        # get the flavor of XBMC
        filesystem = os.environ.get( "OS", "xbox" )
    # return result
    return filesystem

def get_legal_filepath( title, url, mode, download_path, use_title, use_trailer ):
    # create our temp save path
    tmp_path = xbmc.translatePath( "special://temp/%s" % ( os.path.basename( url ), ) )
    # if play_mode is temp download to cache folder
    if ( mode < 2 ):
        filepath = tmp_path
    else:
        # TODO: find a better way
        import re
        # TODO: figure out how to determine download_path's filesystem, statvfs() not available on windows
        # get the filesystem the trailer will be saved to
        filesystem = get_filesystem( download_path )
        # different os's have different illegal characters
        illegal_characters = { "xbox": '\\/:*?"<>|,=;+', "win32": '\\/:*?"<>|', "Linux": "/", "OS X": "/:" }[ filesystem ]
        # get a valid filepath
        if ( use_title ):
            # append "-trailer" if user preference
            title = u"%s%s%s" % ( title, ( u"", u"-trailer", )[ use_trailer ], os.path.splitext( url )[ 1 ], )
        else:
            # append "-trailer" if user preference
            title = u"%s%s%s" % ( os.path.splitext( os.path.basename( url ) )[ 0 ], ( u"", u"-trailer", )[ use_trailer ], os.path.splitext( os.path.basename( url ) )[ 1 ], )
        # clean the filename
        filename = re.sub( '[%s]' % ( illegal_characters, ), u"", title )
        # we need to handle xbox special
        if ( filesystem == "xbox" ):
            # set the length to 37 if filepath isn't a smb share for the .conf file
            if( len( filename ) > 37 and not download_path.startswith( "smb://" ) ):
                name, ext = os.path.splitext( filename )
                filename = name[ : 37 - len( ext ) ].strip() + ext
            # replace any characters whose ord > 127
            for char in filename:
                if ( ord( char ) > 127 ):
                    filename = filename.replace( char, "_" )
        # make our filepath
        filepath = os.path.join( xbmc.translatePath( download_path ), filename )
    # return results
    return unicode( tmp_path, "utf-8" ), filepath
