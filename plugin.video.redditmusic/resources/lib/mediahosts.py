'''
    redditmusic.resources.lib.mediahosts
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module resolves web urls to playable media URLs. Some hosts defer to
    their respective addons (YouTube, Vimeo) and some return a direct URL to
    the media item.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import re
import urlparse
import requests


class _MediaHost(object):
    '''Base class for media hosts. Subclasses must provide an implementation of
    from_url. They should also update the class attribute HOSTS. Optionally,
    the match class method can be overridden as well.
    '''

    HOSTS = []

    @classmethod
    def get_hosts(cls):
        '''Returns a list of hostnames that this media host can parse'''
        return cls.HOSTS

    @classmethod
    def match(cls, url):
        '''Returns True if this class can parse the given url or False
        otherwise.
        '''
        parts = urlparse.urlparse(url)
        if parts.netloc in cls.get_hosts():
            return True
        return False

    @classmethod
    def from_url(cls, url):
        '''Must be overrideen by subclasses. Returns a playable media URL for
        the given browser URL or None if a URL cannot be parsed.
        '''
        raise NotImplementedError


class YouTube(_MediaHost):
    '''Resolves youtube browser URLs to plugin:// urls which can be handled by
    the YouTube addon.
    '''

    HOSTS = [
        'youtube.com',
        'www.youtube.com'
    ]

    @classmethod
    def from_url(cls, url):
        '''Returns a playable URL that will refers to the XBMC YouTube
        addon.
        '''
        parts = urlparse.urlparse(url)
        params = urlparse.parse_qs(parts.query)
        video_id = params['v'][0]
        return cls._play_url(video_id)

    @classmethod
    def _play_url(cls, video_id):
        '''Returns a playable URL for the YouTube plugin for the given
        video_id.
        '''
        ptn = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
        return ptn % video_id


class Vimeo(_MediaHost):
    '''Resolves Vimeo browser URLs to plugin:// urls which can be handled by
    the Vimeo addon.
    '''

    HOSTS = [
        'vimeo.com',
        'www.vimeo.com'
    ]

    @classmethod
    def from_url(cls, url):
        '''Returns a playable Vimeo plugin URL for the given browser URL'''
        video_id = url.split('/')[-1]
        return cls._play_url(video_id)

    @classmethod
    def _play_url(cls, video_id):
        '''Returns a playable URL for the Vimeo plugin for the given
        video_id.
        '''
        ptn = 'plugin://plugin.video.vimeo/?action=play_video&videoid=%s'
        return ptn % video_id


class SoundCloud(_MediaHost):
    '''Resolves SouncCloud browser URLs to playable mp3 URLs.'''

    HOSTS = [
        'soundcloud.com',
        'www.soundcloud.com',
    ]

    PTN = re.compile('"streamUrl":"(.+?)"')

    @classmethod
    def from_url(cls, url):
        '''Returns a URL to an mp3 file found on the provided url's page. This
        method only returns the first mp3 file found on the page. It doesn't
        support multiple files.
        '''
        resp = requests.get(url).content
        match = cls.PTN.search(resp)
        if not match:
            return None
        return match.group(1)


# All avaiable media hosts
HOSTS = [subclass for subclass in _MediaHost.__subclasses__()]

# A list of all hostnames that can be parsed by this module
HOST_STRINGS = []
for host in HOSTS:
    HOST_STRINGS.extend(host.get_hosts())


def resolve(url):
    '''Attempts to returna  playable URL for the given browser URL. Returns
    None if a playable URL cannot be found.
    '''
    for host in HOSTS:
        if host.match(url):
            return host.from_url(url)
    return None
