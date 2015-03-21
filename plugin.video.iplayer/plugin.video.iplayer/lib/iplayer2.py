#!/usr/bin/python

# Python libs
import re, time, os, string, sys
import urllib, urllib2
import traceback
from socket import timeout as SocketTimeoutError
from xml.etree import ElementTree as ET

try:
    from hashlib import md5 as _md5
except:
    # use md5 for python 2.5 compat
    import md5
    _md5 = md5.new

if sys.version_info >= (2, 7):
    import json as _json
else:
    import simplejson as _json

# XBMC libs
import xbmc, xbmcgui

# external libs
import listparser
import stations
import utils
import httplib2

__addoninfo__ = utils.get_addoninfo()
__addon__ = __addoninfo__["addon"]

sys.path.append(os.path.join(__addoninfo__["path"], 'lib', 'httplib2'))
import socks

# me want 2.5!!!
def any(iterable):
     for element in iterable:
         if element:
             return True
     return False

# http://colinm.org/blog/on-demand-loading-of-flickr-photo-metadata
# returns immediately for all previously-called functions
def call_once(fn):
    called_by = {}
    def result(self):
        if self in called_by:
            return
        called_by[self] = True
        fn(self)
    return result

# runs loader before decorated function
def loaded_by(loader):
    def decorator(fn):
        def result(self, *args, **kwargs):
            loader(self)
            return fn(self, *args, **kwargs)
        return result
    return decorator

rss_cache = {}

self_closing_tags = ['alternate', 'mediator']

re_selfclose = re.compile('<([a-zA-Z0-9]+)( ?.*)/>', re.M | re.S)
re_concept_id = re.compile('concept_pid:([a-z0-9]{8})')

def get_proxy():
    proxy_server = None
    proxy_type_id = 0
    proxy_port = 8080
    proxy_user = None
    proxy_pass = None
    try:
        proxy_server = __addon__.getSetting('proxy_server')
        proxy_type_id = __addon__.getSetting('proxy_type')
        proxy_port = int(__addon__.getSetting('proxy_port'))
        proxy_user = __addon__.getSetting('proxy_user')
        proxy_pass = __addon__.getSetting('proxy_pass')
    except:
        pass

    if   proxy_type_id == '0': proxy_type = socks.PROXY_TYPE_HTTP_NO_TUNNEL
    elif proxy_type_id == '1': proxy_type = socks.PROXY_TYPE_HTTP
    elif proxy_type_id == '2': proxy_type = socks.PROXY_TYPE_SOCKS4
    elif proxy_type_id == '3': proxy_type = socks.PROXY_TYPE_SOCKS5

    proxy_dns = True

    return (proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass)

def get_httplib():
    http = None
    try:
        if __addon__.getSetting('proxy_use') == 'true':
            (proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass) = get_proxy()
            utils.log("Using proxy: type %i rdns: %i server: %s port: %s user: %s pass: %s" % (proxy_type, proxy_dns, proxy_server, proxy_port, "***", "***"),xbmc.LOGINFO)
            http = httplib2.Http(proxy_info = httplib2.ProxyInfo(proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass))
        else:
          http = httplib2.Http()
    except:
        raise
        utils.log('Failed to initialize httplib2 module',xbmc.LOGFATAL)

    return http

http = get_httplib()

def fix_selfclosing(xml):
    return re_selfclose.sub('<\\1\\2></\\1>', xml)

def set_http_cache(dir):
    try:
        cache = httplib2.FileCache(dir, safe=lambda x: _md5(x).hexdigest())
        http.cache = cache
    except:
        pass

class NoItemsError(Exception):
    def __init__(self, reason=None):
        self.reason = reason

    def __str__(self):
        reason = self.reason or '<no reason given>'
        return "Programme unavailable ('%s')" % (reason)

class memoize(object):
    def __init__(self, func):
        self.func = func
        self._cache = {}
    def __call__(self, *args, **kwds):
        key = args
        if kwds:
            items = kwds.items()
            items.sort()
            key = key + tuple(items)
        if key in self._cache:
            return self._cache[key]
        self._cache[key] = result = self.func(*args, **kwds)
        return result

def httpretrieve(url, filename):
    data = httpget(url)
    f = open(filename, 'wb')
    f.write(data)
    f.close()

def httpget(url):
    resp = ''
    data = ''
    try:
        start_time = time.clock()
        if http:
            resp, data = http.request(url, 'GET')
        else:
            raise

        sec = time.clock() - start_time
        utils.log('URL Fetch took %2.2f sec for %s' % (sec, url),xbmc.LOGINFO)

        return data
    except:
        traceback.print_exc(file=sys.stdout)
        dialog = xbmcgui.Dialog()
        dialog.ok('Network Error', 'Failed to fetch URL', url)
        utils.log('Network Error. Failed to fetch URL %s' % url,xbmc.LOGINFO)

    return data

def get_provider():
    provider = None
    try:
        provider_id = __addon__.getSetting('provider')
    except:
        pass

    if   provider_id == '1': provider = 'akamai'
    elif provider_id == '2': provider = 'limelight'
    elif provider_id == '3': provider = 'level3'

    return provider

def get_protocol():
    protocol = "rtmp"
    try:
        protocol_id = __addon__.getSetting('protocol')
    except:
        pass

    if protocol_id == '1': protocol = 'rtmpt'

    return protocol

def get_port():
    port = 1935
    protocol = get_protocol()
    if protocol == 'rtmpt': port = 80
    return port

def get_thumb_dir():
    thumb_dir = os.path.join(__addoninfo__['path'], 'resources', 'media')
    if utils.get_os() == "xbox":
        thumb_dir = os.path.join(thumb_dir, 'xbox')
    return thumb_dir

def get_setting_videostream():

    stream = 'h264 1520'

    stream_prefs = '0'
    try:
        stream_prefs = __addon__.getSetting('video_stream')
    except:
        pass

    # Auto|H.264 (480kb)|H.264 (800kb)|H.264 (1500kb)|H.264 (2800kb)
    if stream_prefs == '0':
        environment = os.environ.get( "OS" )
        # check for xbox as we set a lower default for xbox (although it can do 1500kbit streams)
        if environment == 'xbox':
            stream = 'h264 820'
        else:
            # play full HD if the screen is large enough (not all programmes have this resolution)
            Y = int(xbmc.getInfoLabel('System.ScreenHeight'))
            X = int(xbmc.getInfoLabel('System.ScreenWidth'))
            # if the screen is large enough for HD
            if Y > 832 and X > 468:
                stream = 'h264 2800'
    elif stream_prefs == '1':
        stream = 'h264 480'
    elif stream_prefs == '2':
        stream = 'h264 820'
    elif stream_prefs == '3':
        stream = 'h264 1520'
    elif stream_prefs == '4':
        stream = 'h264 2800'

    utils.log("Video stream prefs %s - %s" % (stream_prefs, stream),xbmc.LOGINFO)
    return stream
    
def get_setting_videostream_live():

    stream = '3628'

    stream_prefs = '0'
    try:
        stream_prefs = __addon__.getSetting('video_stream_live')
    except:
        pass

    if stream_prefs == '0':
        environment = os.environ.get( "OS" )
        if environment == 'xbox':
            stream = '923'
        else:
            # play full HD if the screen is large enough (not all programmes have this resolution)
            Y = int(xbmc.getInfoLabel('System.ScreenHeight'))
            X = int(xbmc.getInfoLabel('System.ScreenWidth'))
            # if the screen is large enough for HD
            if Y > 832 and X > 468:
                stream = '3628'
    elif stream_prefs == '1':
        stream = '345'
    elif stream_prefs == '2':
        stream = '501'
    elif stream_prefs == '3':
        stream = '923'
    elif stream_prefs == '4':
        stream = '1470'
    elif stream_prefs == '5':
        stream = '2128'

    utils.log("Video stream prefs %s - %s" % (stream_prefs, stream), xbmc.LOGINFO)
    return stream

def get_setting_audiostream():
    stream = 'Auto'

    stream_prefs = '0'
    try:
        stream_prefs = __addon__.getSetting('audio_stream')
    except:
        pass

    # Auto|AAC (320Kb)|AAC (128Kb)|WMA (128Kb)|AAC (48Kb or 32Kb)
    if stream_prefs == '0':
        # Auto - default to highest bitrate AAC
        stream = 'aac320'
    elif stream_prefs == '1':
        stream = 'aac320'
    elif stream_prefs == '2':
        stream = 'aac128'
    elif stream_prefs == '3':
        # Live feeds have a wma+asx application type
        # In this case the wma9 type is not available, and the plugin should default over to wma+asx
        stream = 'wma9 96'
    elif stream_prefs == '4':
        # As above, live feeds only have a 32Kb AAC stream, which should be defaulted to after trying 48 bit
        stream = 'aac48'

    utils.log("Audio stream prefs %s - %s" % (stream_prefs, stream),xbmc.LOGINFO)
    return stream

class media(object):
    tep = {
        ('captions', 'application/ttaf+xml', None, 'http', None) : 'captions',
        ('video', 'video/mp4', 'h264', 'rtmp', 2800)   : 'h264 2800',
        ('video', 'video/mp4', 'h264', 'rtmp', 1520)   : 'h264 1520',
        ('video', 'video/mp4', 'h264', 'rtmp', 1500)   : 'h264 1500',
        ('video', 'video/mp4', 'h264', 'rtmp', 816)    : 'h264 820',
        ('video', 'video/mp4', 'h264', 'rtmp', 796)    : 'h264 800',
        ('video', 'video/mp4', 'h264', 'rtmp', 480)    : 'h264 480',
        ('video', 'video/mp4', 'h264', 'rtmp', 396)    : 'h264 400',
        ('video', 'video/x-flv', 'vp6', 'rtmp', 512)   : 'flashmed',
        ('video', 'video/x-flv', 'spark', 'rtmp', 800) : 'flashwii',
        ('video', 'video/mpeg', 'h264', 'http', 184)   : 'mobile',
        ('audio', 'audio/mpeg', 'mp3', 'rtmp', 80)     : 'mp3 80',
        ('audio', 'audio/x-scpls', 'mp3', 'http', 48 ) : 'mp3 48',
        ('audio', 'audio/x-scpls', 'mp3', 'http', 128 ): 'mp3 128',
        ('audio', 'audio/mp4',  'aac', 'rtmp', None)   : 'aac',
        ('audio', 'audio/wma',  'wma', 'http', None)   : 'wma',
        ('audio', 'audio/mp4', 'aac', 'rtmp', 320)     : 'aac320',
        ('audio', 'audio/mp4', 'aac', 'rtmp', 128)     : 'aac128',
        ('audio', 'audio/mp4', 'aac', 'rtmp', 64)      : 'aac64',
        ('audio', 'audio/wma', 'wma9', 'http', 96)     : 'wma9 96',
        ('audio', 'audio/wma', 'wma9', 'http', 48)     : 'wma9 48',
        ('audio', 'audio/x-ms-asf', 'wma', 'http', 128): 'wma+asx',
        ('audio', 'audio/mp4', 'aac', 'rtmp', 48)      : 'aac48',
        ('audio', 'audio/mp4', 'aac', 'rtmp', 32)      : 'aac32',
        ('video', 'video/mp4', 'h264', 'http', 516)    : 'iphonemp3'}

    def __init__(self, item, media_node, connection):
        self.item      = item
        self.href      = None
        self.kind      = None
        self.method    = None
        self.width, self.height = None, None
        self.bitrate   = None
        self.mimetype  = None
        self.encoding  = None
        self.connection_protocol = None
        if media_node is not None:
            self.read_media_node(media_node, connection)

    @staticmethod
    def create_from_media_xml(item, xml):
        result = []
        for c in xml.findall('connection'):
            result.append(media(item, xml, c))

        return result

    @property
    def url(self):
        return self.connection_href

    @property
    def application(self):
        """
        The type of stream represented as a string.
        i.e. 'captions', 'flashhd', 'flashhigh', 'flashmed', 'flashwii', 'mobile', 'mp3', 'real', 'aac'
        """
        me = (self.kind, self.mimetype, self.encoding, self.connection_protocol, self.bitrate)
        return self.__class__.tep.get(me, None)

    def read_media_node(self, media, conn):
        """
        Reads media info from a media XML node
        media: media node from BeautifulStoneSoup
        """
        self.kind = media.get('kind')
        self.mimetype = media.get('type')
        self.encoding = media.get('encoding')
        self.width, self.height = media.get('width'), media.get('height')
        self.live = ( media.get('live') == 'true' or self.item.live == True )
        self.service = media.get('service')
        try:
            self.bitrate = int(media.get('bitrate'))
        except:
            if media.get('bitrate') != None:
                utils.log('bitrate = "%s"' % media.get('bitrate'),xbmc.LOGINFO)
            self.bitrate = None

        self.connection_kind = None
        self.connection_live = None
        self.connection_protocol = None
        self.connection_href = None
        self.connection_method = None

        self.connection_kind = conn.get('kind')
        if not self.connection_kind:
            self.connection_kind = conn.get('supplier')
        self.connection_protocol = conn.get('protocol')

        # some akamai rtmp streams (radio) don't specify rtmp protocol
        if self.connection_protocol == None and self.connection_kind == 'akamai':
            self.connection_protocol = 'rtmp'

        if self.connection_kind == 'll_icy':
            self.connection_href = conn.get('href')
            self.connection_protocol = 'http'


        if self.connection_kind in ['http', 'sis', 'asx', 'll_icy']:
            self.connection_href = conn.get('href')
            self.connection_protocol = 'http'
            # world service returns a list to a pls file
            if "worldservice" in self.connection_href:
                pls = httpget(self.connection_href)
                match = re.search("^File1=(.+)$", pls, re.MULTILINE)
                if match:
                    self.connection_href = match.group(1)
                    self.connection_protocol = 'http'
                else:
                    self.connection_href = None
                    self.connection_protocol = None

            if self.kind == 'captions':
                self.connection_method = None

        elif self.connection_protocol == 'rtmp':
            server = conn.get('server')
            identifier = conn.get('identifier')
            auth = conn.get('authString')
            application = conn.get('application')
            # sometimes we don't get a rtmp application for akamai
            if application == None and self.connection_kind == 'akamai':
                application = "ondemand"

            timeout = __addon__.getSetting('stream_timeout')
            swfplayer = 'http://emp.bbci.co.uk/emp/SMPf/1.9.45/StandardMediaPlayerChromelessFlash.swf'
            params = dict(protocol = get_protocol(), port = get_port(), server = server, auth = auth, ident = identifier, app = application)

            if self.connection_kind == 'limelight':
                # note that librtmp has a small issue with constructing the tcurl here. we construct it ourselves for now (fixed in later librtmp)
                self.connection_href = "%(protocol)s://%(server)s:%(port)s/ app=%(app)s?%(auth)s tcurl=%(protocol)s://%(server)s:%(port)s/%(app)s?%(auth)s playpath=%(ident)s" % params
            else:
                # akamai needs the auth string included in the playpath
                self.connection_href = "%(protocol)s://%(server)s:%(port)s/%(app)s?%(auth)s playpath=%(ident)s?%(auth)s" % params

            # swf authention only needed for the ondemand streams
            if self.live:
                self.connection_href += " live=1"
            elif self.kind == 'video':
                self.connection_href += " swfurl=%s swfvfy=1" % swfplayer

            self.connection_href += " timeout=%s" % timeout

        else:
            utils.log("connectionkind %s unknown" % self.connection_kind,xbmc.LOGERROR)

        if self.connection_protocol and __addon__.getSetting('enhanceddebug') == 'true':
            utils.log("protocol: %s - kind: %s - type: %s - encoding: %s, - bitrate: %s" %
                         (self.connection_protocol, self.connection_kind, self.mimetype, self.encoding, self.bitrate),xbmc.LOGINFO)
            utils.log("conn href: %s" % self.connection_href,xbmc.LOGINFO)

    @property
    def programme(self):
        return self.item.programme

class item(object):
    """
    Represents an iPlayer programme item. Most programmes consist of 2 such items,
    (1) the ident, and (2) the actual programme. The item specifies the properties
    of the media available, such as whether it's a radio/TV programme, if it's live,
    signed, etc.
    """

    def __init__(self, programme, item_node):
        """
        programme: a programme object that represents the 'parent' of this item.
        item_node: an XML &lt;item&gt; node representing this item.
        """
        self.programme = programme
        self.identifier = None
        self.service = None
        self.guidance = None
        self.masterbrand = None
        self.alternate = None
        self.duration = ''
        self.medias = None
        self.read_item_node(item_node)

    def read_item_node(self, node):
        """
        Reads the specified XML &lt;item&gt; node and sets this instance's
        properties.
        """
        self.kind = node.get('kind')
        self.identifier = node.get('identifier')
        utils.log('Found item: %s, %s' % (self.kind, self.identifier),xbmc.LOGINFO)
        if self.kind in ['programme', 'radioProgramme']:
            self.live = node.get('live') == 'true'
            #self.title = node.get('title')
            self.group = node.get('group')
            self.duration = node.get('duration')
            #self.broadcast = node.broadcast
            nf = node.find('service')
            if nf is not None: self.service = nf.text and nf.get('id')
            nf = node.find('masterbrand')
            if nf is not None: self.masterbrand = nf.text and nf.get('id')
            nf = node.find('alternate')
            if nf is not None: self.alternate = nf.text and nf.get('id')
            nf = node.find('guidance')
            if nf is not None: self.guidance = nf.text


    @property
    def is_radio(self):
        """ True if this stream is a radio programme. """
        return self.kind == 'radioProgramme'

    @property
    def is_tv(self):
        """ True if this stream is a TV programme. """
        return self.kind == 'programme'

    @property
    def is_ident(self):
        """ True if this stream is an ident. """
        return self.kind == 'ident'

    @property
    def is_programme(self):
        """ True if this stream is a programme (TV or Radio). """
        return self.is_radio or self.is_tv

    @property
    def is_live(self):
        """ True if this stream is being broadcast live. """
        return self.live

    @property
    def is_signed(self):
        """ True if this stream is 'signed' for the hard-of-hearing. """
        return self.alternate == 'signed'

    def get_available_streams(self):
        """
        Returns a list of available streams in order of desirability,
        according to provider and bitrate preferences
        """
        if self.is_tv:
            streams = ['h264 2800', 'h264 1520', 'h264 1500', 'h264 820', 'h264 800', 'h264 480', 'h264 400']
            rate = get_setting_videostream()
        else:
            streams = ['aac320', 'aac128', 'wma9 96', 'mp3 128', 'mp3 80', 'mp3 48', 'wma+asx', 'aac64', 'aac48', 'wma9 48', 'aac32' ]
            rate = get_setting_audiostream()

        provider = get_provider()

        # Build a list of streams of lower or equal bitrate to the config setting
        if rate not in streams:
            return ([], false)

        media = []
        above_limit = False
        for strm in streams[streams.index(rate):]:
            media.extend(self.get_media_list_for(strm, provider))

        # If nothing found, get next highest bitrate
        if len(media) == 0:
            above_limit = True
            i = streams.index(rate)
            while len(media) == 0 and i > 0:
                i -= 1
                media = self.get_media_list_for(streams[i], provider)

        utils.log("Available streams by preference: %s" % (["%s %s" % (m.connection_kind, m.application) for m in media]),xbmc.LOGINFO)

        return (media, above_limit)

    def get_available_streams_live(self):
        url = "http://www.bbc.co.uk/mediaselector/playlists/hds/pc/ak/%s.f4m" % stations.channels_tv_live_mapping[self.programme.pid]
        
        rate = get_setting_videostream_live()

        xml = httpget(url)

        # remove namespace
        xml = re.sub(' xmlns="[^"]+"', '', xml, count=1)

        root = ET.fromstring(xml)
        medias = []
        for media_node in root.getiterator('media'):
            if int(media_node.attrib['bitrate']) <= int(rate):
                live_media = media(self, None, media_node.attrib['bitrate'])
                live_media.connection_href = media_node.attrib['href'].replace('.f4m', '.m3u8')
                live_media.connection_kind = "hls"
                medias.append(live_media)

        medias.reverse()
        return [ medias, False ]

    def mediaselector_url(self):
        v = __addon__.getSetting('mediaselector')
        if v == '0':
            mediaset="pc"
            if self.is_live and self.is_radio:
                mediaset="http-icy-mp3-a"

            url = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/%s/vpid/%s"
            return url % (mediaset, self.identifier)
        else:
            url = "http://open.live.bbc.co.uk/mediaselector/4/mtis/stream/%s"

        return url % self.identifier

    def get_media_list_for(self, stream, provider_pref):
        """
        Returns a list of media objects for the given rate, putting the
        preferred provider first if it exists
        """
        if not self.medias:
            url = self.mediaselector_url()
            utils.log("Stream XML URL: %s" % url,xbmc.LOGINFO)
            xml = httpget(url)
            xml = utils.xml_strip_namespace(xml)
            tree = ET.XML(xml)
            self.medias = []
            for m in tree.findall('media'):
                self.medias.extend(media.create_from_media_xml(self, m))

        result = []
        for m in self.medias:
            if m.application == stream:
                if m.connection_kind == provider_pref:
                    result.insert(0, m)
                else:
                    result.append(m)

        return result

class programme_base(object):

    def __init__(self, pid):
        self.pid = pid

    def get_thumbnail(self, size='large'):
        """
        Returns the URL of a thumbnail.
        size: '640x360'/'biggest'/'largest' or '512x288'/'big'/'large' or None
        """
        template = self.image_base + "%s_%s.jpg"
        if size in ['640x360', '640x', 'x360', 'biggest', 'largest']:
            return template % (self.pid, '640_360')
        elif size in ['512x288', '512x', 'x288', 'big', 'large']:
            return template % (self.pid, '512_288')
        elif size in ['178x100', '178x', 'x100', 'small']:
            return template % (self.pid, '178_100')
        elif size in ['150x84', '150x', 'x84', 'smallest']:
            return template % (self.pid, '150_84')

class programme(programme_base):
    """
    Represents an individual iPlayer programme, as identified by an 8-letter PID,
    and contains the programme title, subtitle, broadcast time and list of playlist
    items (e.g. ident and then the actual programme.)
    """

    def __init__(self, pid):
        super(programme, self).__init__(pid)
        self.meta = {}
        self._items = []
        self._related = []

    @call_once
    def read_playlist(self):
        utils.log('Read playlist for %s...' % self.pid,xbmc.LOGINFO)
        self.parse_playlist(self.playlist)

    def get_playlist_xml(self):
        """ Downloads and returns the XML for a PID from the iPlayer site. """
        try:
            url = self.playlist_url
            xml = httpget(url)
            return xml
        except SocketTimeoutError:
            utils.log("Timed out trying to download programme XML",xbmc.LOGERROR)
            raise

    def parse_playlist(self, xmlstr):
        xmlstr = utils.xml_strip_namespace(xmlstr)
        tree = ET.XML(xmlstr)

        self.meta = {}
        self._items = []
        self._related = []

        utils.log('Found programme: %s' % tree.find('title').text,xbmc.LOGINFO)
        self.meta['title'] = tree.find('title').text
        self.meta['summary'] = tree.find('summary').text

        for link in tree.findall('link'):
            if link.attrib['rel'] == 'holding':
                self.meta['thumbnail'] = link.attrib['href']
                break

        # Live radio feeds have no text node in the summary node
        if self.meta['summary'] is not None:
            self.meta['summary'].lstrip(' ')
        self.meta['date'] = tree.find('updated').text

        if tree.find('noitems'):
            utils.log('No playlist items: %s' % tree.find('noitems').get('reason'),xbmc.LOGINFO)
            self.meta['reason'] = tree.find('noitems').get('reason')

        self._items = [item(self, i) for i in tree.findall('item')]

        for link in tree.findall('relatedlink'):
            i = {}
            i['title'] = link.find('title').text
            #i['summary'] = item.summary # FIXME looks like a bug in BSS
            i['pid'] = (re_concept_id.findall(link.find('id').text) or [None])[0]
            i['programme'] = programme(i['pid'])
            self._related.append(i)

    def get_url(self):
        """
        Returns the programmes episode page.
        """
        return "http://www.bbc.co.uk/iplayer/episode/%s" % (self.pid)

    def get_thumbnail(self, size='large'):
        if self.meta['thumbnail']:
            return self.meta['thumbnail'] 
        else:
            return super(programme, self).get_thumbnail(size)

    @property
    def playlist_url(self):
        return "http://www.bbc.co.uk/iplayer/playlist/%s" % self.pid

    @property
    def playlist(self):
        return self.get_playlist_xml()

    def get_date(self):
        return self.meta['date']

    @loaded_by(read_playlist)
    def get_title(self):
        return self.meta['title']

    @loaded_by(read_playlist)
    def get_summary(self):
        return self.meta['summary']

    @loaded_by(read_playlist)
    def get_related(self):
        return self._related

    @loaded_by(read_playlist)
    def get_items(self):
        if not self._items:
            raise NoItemsError(self.meta['reason'])
        return self._items

    @property
    def programme(self):
        for i in self.items:
            if i.is_programme:
                return i
        return None

    title = property(get_title)
    summary = property(get_summary)
    date = property(get_date)
    thumbnail = property(get_thumbnail)
    related = property(get_related)
    items = property(get_items)

#programme = memoize(programme)


class programme_simple(programme_base):
    """
    Represents an individual iPlayer programme, as identified by an 8-letter PID,
    and contains the programme pid, title, subtitle etc
    """

    def __init__(self, pid, entry):
        super(programme_simple, self).__init__(pid)
        self.meta = {}
        self.meta['title'] = entry.title
        if entry.summary is not None:
            self.meta['summary'] = string.lstrip(entry.summary, ' ')
        self.meta['date'] = entry.date
        self.categories = []
        for c in entry.categories:
            #if c != 'TV':
            self.categories.append(c.rstrip())
        self._items = []
        self._related = []
        self.series = entry.series
        self.episode = entry.episode
        self.image_base = entry.image_base

    @call_once
    def read_playlist(self):
        pass

    def get_playlist_xml(self):
        pass

    def parse_playlist(self, xml):
        pass

    def get_url(self):
        """
        Returns the programmes episode page.
        """
        return "http://www.bbc.co.uk/iplayer/episode/%s" % (self.pid)

    @property
    def playlist_url(self):
        return "http://www.bbc.co.uk/iplayer/playlist/%s" % self.pid

    @property
    def playlist(self):
        return self.get_playlist_xml()

    def get_thumbnail(self, size='large'):
        return super(programme_simple, self).get_thumbnail(size)

    def get_date(self):
        return self.meta['date']

    @loaded_by(read_playlist)
    def get_title(self):
        return self.meta['title']

    @loaded_by(read_playlist)
    def get_summary(self):
        return self.meta['summary']

    @loaded_by(read_playlist)
    def get_related(self):
        return self._related

    @loaded_by(read_playlist)
    def get_items(self):
        if not self._items:
            raise NoItemsError(self.meta['reason'])
        return self._items

    @property
    def programme(self):
        for i in self.items:
            if i.is_programme:
                return i
        return None

    title = property(get_title)
    summary = property(get_summary)
    date = property(get_date)
    thumbnail = property(get_thumbnail)
    related = property(get_related)
    items = property(get_items)


class feed(object):
    def __init__(self, tvradio=None, channel=None, category=None, atoz=None, date=None, searchterm=None, radio=None, live=False, listing=None):
        """
        Creates a feed for the specified channel/category/whatever.
        tvradio: type of channel - 'tv' or 'radio'. If a known channel is specified, use 'auto'.
        channel: name of channel, e.g. 'bbc_one'
        category: category name, e.g. 'drama'
        subcategory: subcategory name, e.g. 'period_drama'
        atoz: A-Z listing for the specified letter
        """
        if tvradio == 'auto':
            if not channel and not searchterm:
                raise Exception, "Must specify channel or searchterm when using 'auto'"
            elif channel in stations.channels_tv:
                self.tvradio = 'tv'
            elif channel in stations.channels_radio:
                self.tvradio = 'radio'
            else:
                raise Exception, "TV channel '%s' not recognised." % self.channel

        elif tvradio in ['tv', 'radio']:
            self.tvradio = tvradio
        else:
            self.tvradio = None

        self.format = 'json'
        self.channel = channel
        self.category = category
        self.atoz = atoz
        self.date = date
        self.searchterm = searchterm
        self.radio = radio
        self.live = live
        self.listing = listing

    def create_url(self):

        if __addon__.getSetting('listings_cache_disable') == 'false':
            if self.listing == 'list' and self.channel:
                return "http://iplayer.xbmc4xbox.org.uk/" + self.channel + '.json'

        params = []
        if self.listing == 'categories':
            params = [ 'categorynav' ] 
        elif self.listing == 'atoz':
            params = [ 'atoz']
            params += [ 'letter', self.atoz ]
        elif self.listing == 'bydate':
            params = [ 'schedule']
            params += [ 'date', self.date ]
            params += [ 'allow_unavailable', '0' ]
        elif self.listing == 'popular':
            params = [ 'mostpopular' ]
        elif self.listing == 'highlights':
            params = [ 'featured' ]
        elif self.listing == 'latest':
            params = [ 'latest' ]
            params += [ 'limit', '20' ]
        elif self.searchterm:
            params = [ 'search' ]
            params += [ 'q', urllib.quote_plus(self.searchterm) ]
        elif self.listing == 'list':
            params = [ 'listview' ]
            if self.category:
                params += [ 'category', self.category ]
            if self.date:
                params += [ 'date', self.category ]

        if self.channel: params += [ 'masterbrand', self.channel ]
        if self.tvradio: params += [ 'service_type', self.tvradio ]

        params = params + [ 'format', self.format ]

        url = "http://www.bbc.co.uk/iplayer/ion/" + '/'.join(params)
        return url


    def get_name(self, separator=' '):
        """
        A readable title for this feed, e.g. 'BBC One' or 'TV Drama' or 'BBC One Drama'
        separator: string to separate name parts with, defaults to ' '. Use None to return a list (e.g. ['TV', 'Drama']).
        """
        path = []

        # if got a channel, don't need tv/radio distinction
        if self.channel:
            assert self.channel in stations.channels_tv or self.channel in stations.channels_radio, 'Unknown channel'
            if self.tvradio == 'tv':
                path.append(stations.channels_tv.get(self.channel, '(TV)'))
            else:
                path.append(stations.channels_radio.get(self.channel, '(Radio)'))

        if separator != None:
            return separator.join(path)
        else:
            return path

    def channels(self):
        """
        Return a list of available channels.
        """
        if self.channel: return None
        if self.tvradio == 'tv': return stations.channels_tv_list
        if self.tvradio == 'radio':
            if radio:
                return channels_radio_type_list[radio]
            else:
                return stations.channels_radio_list
        return None

    def channels_feed(self):
        """
        Return a list of available channels as a list of feeds.
        """
        if self.channel or self.atoz:
            return None
        if self.tvradio == 'tv':
            if self.live:
                channels = []
                for (ch, title) in stations.channels_tv_list:
                    if ch in stations.channels_tv_live_mapping:
                        channels.append(feed('tv', channel=ch))
                return channels
            else:
                return [feed('tv', channel=ch) for (ch, title) in stations.channels_tv_list]
        if self.tvradio == 'radio':
            if self.radio:
                return [feed('radio', channel=ch) for (ch, title) in stations.channels_radio_type_list[self.radio]]
            else:
                return [feed('radio', channel=ch) for (ch, title) in stations.channels_radio_list]
        return None

    def read_rss(self, url):
        utils.log('Read File: %s' % url,xbmc.LOGINFO)
        if url not in rss_cache:
            utils.log('File not in cache, requesting...',xbmc.LOGINFO)
            xml = httpget(url)
            progs = listparser.parse(xml, self.format)
            if not progs: return []
            d = []
            for entry in progs.entries:
                p = programme_simple(entry.id, entry)
                d.append(p)
            utils.log('Found %d entries' % len(d),xbmc.LOGINFO)
            rss_cache[url] = d
        else:
            utils.log('File found in cache',xbmc.LOGINFO)
        return rss_cache[url]

    def list(self):
        return self.read_rss(self.create_url())

    def categories(self):
        categories = []
        url = self.create_url()
        data = httpget(url)

        if self.format == 'xml':
            # remove namespace
            data = utils.xml_strip_namespace(data)

            root = ET.fromstring(data)
            categories = []
            for category in root.getiterator('category'):
                id = category.find('id').text
                text = category.find('text').text
                categories.append([ text, id ])

        if self.format == 'json':
            json = _json.loads(data)

            for parent in json['blocklist']:
                id = parent['id']
                text = parent['text']
                categories.append([ text, id ])
                if 'child_categories' in parent:
                    for child in parent['child_categories']:
                        id = child['id']
                        text = child['text']
                        categories.append([ text, id ])

        return categories

    
    @property
    def is_radio(self):
        """ True if this feed is for radio. """
        return self.tvradio == 'radio'

    @property
    def is_tv(self):
        """ True if this feed is for tv. """
        return self.tvradio == 'tv'

    name = property(get_name)

tv = feed('tv')
radio = feed('radio')

def test():
    tv = feed('tv')
    print tv.popular()
    print tv.channels()
    print tv.get('bbc_one')
    print tv.get('bbc_one').list()
    for c in tv.get('bbc_one').categories():
        print c
    #print tv.get('bbc_one').channels()
    #print tv.categories()
    #print tv.get('drama').list()
    #print tv.get('drama').get_subcategory('period').list()

if __name__ == '__main__':
    test()
