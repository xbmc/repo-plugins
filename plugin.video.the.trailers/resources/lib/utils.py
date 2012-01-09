# main imports
import os
import sys
import xbmc
import xbmcaddon
import xbmcvfs
import socket
import xbmcgui
import xbmcaddon
import unicodedata
import simplejson
import urllib2

# Retrieve add-on specified detials
__addon__       = xbmcaddon.Addon()
__addonid__     = ( sys.modules[ "__main__" ].__addonid__ )
__addonname__   = ( sys.modules[ "__main__" ].__addonname__ )
__author__      = ( sys.modules[ "__main__" ].__author__ )
__version__     = ( sys.modules[ "__main__" ].__version__ )
__addonpath__   = ( sys.modules[ "__main__" ].__addonpath__ )
__localize__    = __addon__.getLocalizedString

### import libraries
from urllib2 import HTTPError, URLError, urlopen
from resources.lib.script_exceptions import *
#HTTP404Error, HTTP503Error, DownloadError, HTTPTimeout

### adjust default timeout to stop script hanging
timeout = 20
socket.setdefaulttimeout(timeout)
### Declare dialog
dialog = xbmcgui.DialogProgress()

# Fixes unicode problems
def _unicode( text, encoding='utf-8' ):
    try: text = unicode( text, encoding )
    except: pass
    return text

def _normalize_string( text ):
    try: text = unicodedata.normalize( 'NFKD', _unicode( text ) ).encode( 'ascii', 'ignore' )
    except: pass
    return text

# Log message
def log( txt, severity=xbmc.LOGDEBUG, heading=False ):

    """Log to txt xbmc.log at specified severity"""
    try:
        if ( heading ):
            xbmc.log( "-" * 70, level=severity )
        message = ('%s: %s' % (__addonname__,txt) )
        xbmc.log(msg=message, level=severity)
        if ( heading ):
            xbmc.log( "-" * 70, level=severity )        
    except UnicodeEncodeError:
        try:
            message = _normalize_string('%s: %s' %(__addonname__,txt) )
            xbmc.log(msg=message, level=severity)
        except:
            message = ('%s: UnicodeEncodeError' %__addonname__ )
            xbmc.log(msg=message, level=xbmc.LOGWARNING)
        
        
def get_filesystem( download_path ):
    # use win32 illegal characters for smb shares to be safe (eg run on linux, save to windows)
    if ( download_path.startswith( "smb://" ) ):
        filesystem = "win32"
    else:
        # get the flavor of XBMC
        filesystem = os.environ.get( "OS" )
    # return result
    return filesystem

def get_legal_filepath( title, url, mode, download_path, use_title, use_trailer ):
    # create our temp save path
    addondir = xbmc.translatePath( __addon__.getAddonInfo('profile') )
    tempdir = os.path.join(addondir, 'temp')
    xbmcvfs.mkdir(tempdir)
    tmp_path = os.path.join( tempdir, os.path.basename( url ) )
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
        illegal_characters = { "win32": '\\/:*?"<>|', "Linux": "/", "OS X": "/:" }[ filesystem ]
        # get a valid filepath
        if ( use_title ):
            # append "-trailer" to title if user preference
            title = u"%s%s%s" % ( title, ( u"", u"-trailer", )[ use_trailer ], os.path.splitext( url )[ 1 ], )
        else:
            # append "-trailer" if user preference
            title = u"%s%s%s" % ( os.path.splitext( os.path.basename( url ) )[ 0 ], ( u"", u"-trailer", )[ use_trailer ], os.path.splitext( os.path.basename( url ) )[ 1 ], )
        # clean the filename
        filename = re.sub( '[%s]' % ( illegal_characters, ), u"", title )
        # make our filepath
        filepath = os.path.join( xbmc.translatePath( download_path ), filename )
    # return results
    return tmp_path, filepath

# Define dialogs
def _dialog(action, percentage = 0, line0 = '', line1 = '', line2 = '', line3 = '', background = False):
    if not line0 == '':
        line0 = __addonname__ + line0
    else:
        line0 = __addonname__
    if not background:
        if action == 'create':
            dialog.create( __addonname__, line1, line2, line3 )
        if action == 'update':
            dialog.update( percentage, line1, line2, line3 )
        if action == 'close':
            dialog.close()
        if action == 'iscanceled':
            if dialog.iscanceled():
                return True
            else:
                return False
        if action == 'okdialog':
            xbmcgui.Dialog().ok(line0, line1, line2, line3)
    if background:
        if (action == 'create' or action == 'okdialog'):
            if line2 == '':
                msg = line1
            else:
                msg = line1 + ': ' + line2
            xbmc.executebuiltin("XBMC.Notification(%s, %s, 7500, %s)" % (line0, msg, __icon__))

# order preserving and get unique entry
def _getUniq(seq):
    seen = []
    result = []
    for item in seq:
        if item in seen: continue
        seen.append( item )
        result.append( item )
    return result

# Retrieve JSON data from cache function
def _get_json(url):
    result = cache.cacheFunction( _get_json_new, url )
    if len(result) == 0:
        result = []
        return result
    else:
        return result[0]

# Retrieve JSON data from site
def _get_json_new(url):
    _log('API: %s'% url)
    try:
        request = urllib2.Request(url)
        request.add_header("Accept", "application/json")
        req = urllib2.urlopen(request) 
        json_string = req.read()
        req.close()
    except HTTPError, e:
        if e.code == 404:
            raise HTTP404Error(url)
        elif e.code == 503:
            raise HTTP503Error(url)
        else:
            raise DownloadError(str(e))
    except:
        json_string = []
    try:
        parsed_json = simplejson.loads(json_string)
    except:
        parsed_json = []
    return [parsed_json]

# Retrieve XML data from cache function
def _get_xml(url):
    result = cache.cacheFunction( _get_xml_new, url )
    if len(result) == 0:
        result = []
        return result
    else:
        return result[0]

# Retrieve XML data from site
def _get_xml_new(url):
    try:
        client  = urlopen(url)
        data    = client.read()
        client.close()
        return data
    except HTTPError, e:
        if e.code   == 404:
            raise HTTP404Error( url )
        elif e.code == 503:
            raise HTTP503Error( url )
        elif e.code == 400:
            raise HTTP400Error( url )
        else:
            raise DownloadError( str(e) )
    except URLError:
        raise HTTPTimeout( url )
    except socket.timeout, e:
        raise HTTPTimeout( url )

# Clean filenames for illegal character in the safest way for windows
def _clean_filename( filename ):
    illegal_char = '<>:"/\|?*'
    for char in illegal_char:
        filename = filename.replace( char , '' )
    return filename