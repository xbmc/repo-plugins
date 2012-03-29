'''This module is used to extract media urls from a page's source. The
BaseVideoHost classes are not meant to be instantiated directly. Only the
resolve function is meant to be called directly.

'''
import re
import urllib
from cgi import parse_qs
from inspect import isclass


def _download(url):
    '''Returns the response from the GET request for a given url.'''
    conn = urllib.urlopen(url)
    resp = conn.read()
    conn.close()
    return resp


# _unhex modeled after python's urllib.unquote
_hextochr = dict(('%02x' % i, chr(i)) for i in range(256))
_hextochr.update(('%02X' % i, chr(i)) for i in range(256))


def _unhex(inp):
    '''Returns a new string, unescaping any instances of hex encoded
    characters.

    >>> _unhex(r'abc\x20def')
    'abc def'

    '''
    res = inp.split(r'\x')
    for i in xrange(1, len(res)):
        item = res[i]
        try:
            res[i] = _hextochr[item[:2]] + item[2:]
        except KeyError:
            res[i] = '%' + item
        except UnicodeDecodeError:
            res[i] = unichr(int(item[:2], 16)) + item[2:]
    return ''.join(res)


class BaseVideoHost(object):
    '''Abstract base class for video host resolvers. Subclasses must override
    the match and resolve methods and should be callable as @classmethods.

    '''

    @classmethod
    def match(cls, src):
        '''Return True or False if cls is able to resolve a media url for the
        given src.

        '''
        raise NotImplementedError

    @classmethod
    def resolve(cls, src):
        '''Return a media url or None for the given src.'''
        raise NotImplementedError


class YouTube(BaseVideoHost):
    '''Media resolver for http://www.youtube.com'''
    _patterns = [
        # (x, y)
        #     x: text pattern to check for existence of a youtube video
        #     y: regular expression that captures the youtube video id in
        #        match.group(1)
        ('http://www.youtube.com/embed/',
         re.compile(r'http://www.youtube.com/embed/([^\?"]+)')),
        ('http://www.youtube.com/p/',
         re.compile(r'http://www.youtube.com/p/([^&\?"]+)')),
        ('http://www.youtube.com/v/',
         re.compile(r'http://www.youtube.com/v/([^&\?"]+)')),
    ]

    @classmethod
    def match(cls, src):
        '''Returns True if a youtube video is found embedded in the provided
        src.

        '''
        for ptn, _ in cls._patterns:
            if ptn in src:
                return True
        return False

    @classmethod
    def resolve(cls, src):
        '''Retuns a playable XBMC media url pointing to the YouTube plugin or
        None.

        '''
        url_ptn = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
        for _, ptn in cls._patterns:
            match = ptn.search(src)
            if match:
                return url_ptn % match.group(1)
        return None


class GoogleVideo(BaseVideoHost):
    '''Media resolver for http://video.google.com'''

    @classmethod
    def match(cls, src):
        '''Returns True if a google video url is found in the page.'''
        return 'http://video.google.com' in src

    @classmethod
    def resolve(cls, src):
        '''Returns a media url for a google video found in the provided src.
        Returns None if the media url cannot be resolved.

        '''
        match = re.search(
                r'http://video.google.com/googleplayer.swf\?docid=(.+?)&', src)
        if match:
            return cls._get_media_url(
                   'http://video.google.com/videoplay?docid=%s' %
                   match.group(1))
        return None

    @classmethod
    def _get_media_url(cls, url):
        '''Returns the the media url for a given google video URL or None.'''
        flvurl_match = re.search(r'preview_url:\'(.+?)\'', _download(url))
        if not flvurl_match:
            return None

        flvurl = _unhex(flvurl_match.group(1))
        params = parse_qs(flvurl.split('?', 1)[1])
        return urllib.unquote_plus(params['videoUrl'][0])


class Vimeo(BaseVideoHost):
    '''Resolver for http://vimeo.com'''

    @classmethod
    def match(cls, src):
        '''Searches for the vimeo swf URL or finds an embedded iframe url.'''
        return ('http://vimeo.com/moogaloop.swf' in src or
                'http://player.vimeo.com/video/' in src)

    @classmethod
    def resolve(cls, src):
        '''Extracts a vimeo video id from the source and returns a playable
        XBMC URL to the Vimeo pluign.

        '''
        match = re.search(r'http://vimeo.com/moogaloop.swf\?clip_id=(.+?)&',
                          src)
        if not match:
            match = re.search('http://player.vimeo.com/video/(.+?)"', src)
        if match:
            return ('plugin://plugin.video.vimeo/?action=play_video&videoid=%s'
                    % match.group(1))
        return None


# Populate the list of available video hosts to match against. Get any class
# that is a subclass of BaseVideoHost but do not include BaseVideoHost itself!
AVAILABLE_HOSTS = [attr_value for attr_name, attr_value in locals().items()
                   if isclass(attr_value) and attr_name != 'BaseVideoHost' and
                   issubclass(attr_value, BaseVideoHost)]


def resolve(src):
    '''Attempts to return a media url for the given page's source.

    First loops through all available hosts stopping at the first host that
    returns True when HOST.match(src) is called. Then host.resolve(src) is
    called to compute the actual media url.

    '''
    for host in AVAILABLE_HOSTS:
        if host.match(src):
            return host.resolve(src)
    return None
