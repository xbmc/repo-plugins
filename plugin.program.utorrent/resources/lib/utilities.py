import urllib, urllib2, cookielib, sys, os
from base64 import b64encode
import xbmc

DEBUG_MODE = 3

__addonname__ = sys.modules[ "__main__" ].__addonname__
__addon__ = sys.modules[ "__main__" ].__addon__
__language__ = sys.modules[ "__main__" ].__language__

# base paths
BASE_DATA_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "addon_data", os.path.basename( os.getcwd() ) )
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
COOKIEFILE = os.path.join( BASE_DATA_PATH, "uTorrent_cookies" )

# Log status codes
LOG_INFO, LOG_ERROR, LOG_NOTICE, LOG_DEBUG = range( 1, 5 )

def _create_base_paths():
    """ creates the base folders """
    if ( not os.path.isdir( BASE_DATA_PATH ) ):
        os.makedirs( BASE_DATA_PATH )
_create_base_paths()

def LOG( status, format, *args ):
    if ( DEBUG_MODE >= status ):
        xbmc.output( "%s: %s\n" % ( ( "INFO", "ERROR", "NOTICE", "DEBUG", )[ status - 1 ], format % args, ) )

def MultiPart(fields,files,ftype) :
    Boundary = '----------ThIs_Is_tHe_bouNdaRY_---$---'
    CrLf = '\r\n'
    L = []

    ## Process the Fields required..
    for (key, value) in fields:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    ## Process the Files..
    for (key, filename, value) in files:
        L.append('--' + Boundary)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        ## Set filetype based on .torrent or .nzb files.
        if ftype == 'torrent':
            filetype = 'application/x-bittorrent'
        else:
            filetype = 'text/xml'
        L.append('Content-Type: %s' % filetype)
        ## Now add the actual Files Data
        L.append('')
        L.append(value)
    ## Add End of data..
    L.append('--' + Boundary + '--')
    L.append('')
    ## Heres the Main stuff that we will be passing back..
    post = CrLf.join(L)
    content_type = 'multipart/form-data; boundary=%s' % Boundary
    ## Return the formatted data..
    return content_type, post

class Client(object):
    def __init__(self, address='localhost', port='8080', user=None, password=None):
        base_url = 'http://' + address + ':' + port
        self.url = base_url + '/gui/'
        if user:
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(realm=None, uri=self.url, user=user, passwd=password)
            self.MyCookies = cookielib.LWPCookieJar()
            if os.path.isfile(COOKIEFILE) : self.MyCookies.load(COOKIEFILE)
            opener = urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.MyCookies)
                , urllib2.HTTPBasicAuthHandler(password_manager)
                )
            opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1) chromeframe/4.0')]
            urllib2.install_opener(opener)

    def HttpCmd(self, urldta, postdta=None, content=None):
        LOG( LOG_DEBUG, "%s %s::url: %s", __addonname__, 'HttpCmd', urldta)
        ## Standard code

        req = urllib2.Request(urldta,postdta)

        ## Process only if Upload..
        if content != None   :
                req.add_header('Content-Type',content)
                req.add_header('Content-Length',str(len(postdta)))

        response = urllib2.urlopen(req)
        link=response.read()
        LOG( LOG_DEBUG, "%s %s::data: %s", __addonname__, 'HttpCmd', str(link))
        response.close()
        self.MyCookies.save(COOKIEFILE)
        return link


