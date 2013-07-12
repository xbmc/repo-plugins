import os, sys, time, socket, urllib, urllib2, urlparse, httplib, hashlib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')

APIKEY       = 'c5f4a7573343137ac1559a86b3a051ec'
APISECRET    = '4fa04cd85a9c9d5b08a931cfb77b40ed'
APIURL       = 'http://ws.audioscrobbler.com/2.0/'
AUTHURL      = 'https://ws.audioscrobbler.com/2.0/'
HEADERS      = {'User-Agent': 'XBMC Media center', 'Accept-Charset': 'utf-8'}
LANGUAGE     = __addon__.getLocalizedString
ADDONVERSION = __addon__.getAddonInfo('version')
CWD          = __addon__.getAddonInfo('path').decode("utf-8")
DATAPATH     = xbmc.translatePath( 'special://profile/addon_data/%s' % __addonid__ ).decode("utf-8")
WINDOW       = xbmcgui.Window(10000)

socket.setdefaulttimeout(10)

def log(txt, session):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s - %s: %s' % (__addonid__, session, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

def parse_argv():
    # parse argv
    try:
        # started as plugin
        params = {}
        paramstring = sys.argv[2]
        if paramstring:
            splitparams = paramstring.lstrip('?').split('&')
            for item in splitparams:
                item = urllib.unquote_plus(item)
                keyval = item.split('=')
                params[keyval[0]] = keyval[1]
        return False, params
    except:
        # started as script
        params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        return True, params

def read_settings(session, puser=False, ppwd=False):
    # read settings
    settings = {}
    user      = __addon__.getSetting('lastfmuser').decode("utf-8")
    pwd       = __addon__.getSetting('lastfmpass').decode("utf-8")
    songs     = __addon__.getSetting('lastfmsubmitsongs') == 'true'
    radio     = __addon__.getSetting('lastfmsubmitradio') == 'true'
    confirm   = __addon__.getSetting('lastfmconfirm') == 'true'
    sesskey   = __addon__.getSetting('sessionkey')
    # if puser or ppwd is true, we were called by onSettingsChanged
    if puser or ppwd:
        # check if user has changed it's username or password
        if (puser != user) or (ppwd != pwd):
            # username or password changed, we need to get a new sessionkey
            sesskey = False
    # get a session key if needed
    if user and pwd and (not sesskey):
        # collect post data
        data = {}
        data['username'] = user
        data['password'] = pwd
        data['method'] = 'auth.getMobileSession'
        response = lastfm.post(data, session, True)
        if not response:
            sesskey = ''
        elif response.has_key('session'):
            sesskey = response['session']['key']
            # set property for skins
            xbmcgui.Window( 10000 ).setProperty('LastFM.CanLove', 'true')
        elif response.has_key('error'):
            msg  = response['message'] 
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), msg, 7000))
            log('Last.fm returned failed response: %s' % msg, session)
            sesskey = ''
        else:
            log('Last.fm an unknown authentication response', session)
            sesskey = ''
        if sesskey:
            __addon__.setSetting('sessionkey', sesskey)
    elif not (user and pwd):
        # no username or password
        xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32027), 7000))
    settings['user']    = user
    settings['pwd']     = pwd
    settings['songs']   = songs
    settings['radio']   = radio
    settings['confirm'] = confirm
    settings['sesskey'] = sesskey
    if sesskey:
        set_prop('LastFM.CanLove', 'True')
    return settings

def set_prop(key, val):
    # set property for skins
    WINDOW.setProperty(key, val)

def get_prop(key):
    # get skin property
    val = WINDOW.getProperty(key)
    return val

def clear_prop(key):
    # clear skin property
    val = WINDOW.clearProperty(key)
    return val

def read_file( item ):
    # read the queue file if we have one
    path = os.path.join(DATAPATH, item)
    if xbmcvfs.exists( path ):
        f = open(path, 'r')
        data =  f.read() 
        if data:
            data = eval(data)
        f.close()
        return data
    else:
        return None

def write_file( item, data ):
    # create the data dir if needed
    if not xbmcvfs.exists( DATAPATH ):
        xbmcvfs.mkdir( DATAPATH )
    # save data to file
    queue_file = os.path.join(DATAPATH, item)
    f = open(queue_file, 'w')
    f.write(repr(data))
    f.close()

def md5sum(txt):
    # generate a md5 hash
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    md5hash = hashlib.md5()
    md5hash.update(txt.encode("utf-8"))
    return md5hash.hexdigest()

def getsig( params ):
    # dict to list
    siglist = params.items()
    # signature params need to be sorted
    siglist.sort()
    # create signature string
    sigstring = ''.join(map(''.join,siglist))
    # add api secret and create a request signature
    sig = md5sum(sigstring + APISECRET)
    return sig

def jsonparse( response ):
    # parse response
    data = unicode(response, 'utf-8', errors='ignore')
    return simplejson.loads(data)

def drop_sesskey():
    # drop our key, this will trigger onsettingschanged to fetch a new key
    __addon__.setSetting('sessionkey', '')

def apibug(items):
    # api bug - if there's only one result, it's not returned as a list
    if isinstance (items,dict):
        temp = []
        temp.append(items)
        items = temp
    return items

class LastFM:
    def __init__( self ):
        pass

    def post( self, params, session, auth=False ):
        # add our api key
        params['api_key'] = APIKEY
        # create a signature
        apisig = getsig(params)
        # add response format
        params['format'] = 'json'
        # add api signature
        params['api_sig'] = apisig
        # get the url we need
        if auth:
            baseurl = AUTHURL
        else:
            baseurl = APIURL
        # encode the data
        str_params = {}
        for k, v in params.iteritems():
            str_params[k] = unicode(v).encode('utf-8')
        data = urllib.urlencode(str_params)
        # prepare post data
        url = urllib2.Request(baseurl, data, HEADERS)
        return self.connect(url, session)

    def get( self, params, session ):
        # create request url
        url = APIURL + '?method=' + params[0] + '&' + params[2] + '=' + params[1].replace(' ', '%20') + '&api_key=' + APIKEY + '&format=json'
        log('list url %s' % url, session)
        return self.connect(url, session)

    def connect( self, url, session ):
        # connect to last.fm
        try:
            req = urllib2.urlopen(url)
            result = req.read()
            req.close()
        except:
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE(32011), LANGUAGE(32026), 7000))
            log('Failed to connect to Last.fm', session)
            return
        log('response %s' % result, session)
        return jsonparse(result)

    def redirect( self, url ):
        # get the redirected url
        try:
            spliturl = urlparse.urlparse(url,allow_fragments=True)
            conn = httplib.HTTPConnection(spliturl.netloc)
            path = spliturl.path
            conn.request("GET", path)
            res = conn.getresponse()
            headers = dict(res.getheaders())
            realurl = headers['location']
            return realurl
        except:
            return ''

lastfm = LastFM()
