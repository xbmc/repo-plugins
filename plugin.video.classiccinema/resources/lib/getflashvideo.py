'''
This module is meant to abstract the parsing of flash video URLs out of plugins.

Each class represents a video site and should implement a @staticmethod named
get_flashvide_url. The method should take 1 argument, a string, usually corresponding
to HTML source code. The method should return a url for a video resource or None if
the page wasn't able to be parsed.
'''
import urllib
import re
import json
import urlparse
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS
from xbmcswift2 import download_page, unhex


def get_flashvideo_url(src=None, url=None):
    if not url and not src:
        print 'At least src or url required.'

    if url:
        src = download_page(url)

    #there are 2 kinds of videos on the site, google video and archive.org
    if src.find('googleplayer') > 0:
        flash_url = GoogleVideo.get_flashvideo_url(src)
    elif src.find('flowplayer') > 0:
        flash_url = ArchiveVideo.get_flashvideo_url(src)
    elif src.find('youtube') > 0:
        flash_url = YouTube.get_flashvideo_url(src)
    else:
        print 'no handler implementd for this url.'

    return flash_url



class YouTube(object):
    @staticmethod
    def get_flashvideo_url(src):
        # Check for youtube
        yt_ptn = re.compile(r'http://www.youtube.com/embed/(.+?)\?')
        match = yt_ptn.search(src)
        if match:
            return 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % match.group(1)
        return None


class GoogleVideo(object):
    @staticmethod
    def get_flashvideo_url(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        url = embed_tags.find('embed')['src']
        docid = urlparse.parse_qs(url.split('?', 1)[1]).get('docid')[0]
        url = 'http://video.google.com/videoplay?docid=%s&hl=en' % docid

        #load the googlevideo page for a given docid or googlevideo swf url
        src = download_page(url)
        flvurl_pattern = re.compile(r"preview_url:'(.+?)'")
        m = flvurl_pattern.search(src)
        if not m:
            return
        previewurl = m.group(1)

        #replace hex things
        # videoUrl\x3dhttp -> videoUrl=http
        previewurl = unhex(previewurl)
        #parse querystring and return the videoUrl
        params = urlparse.parse_qs(previewurl.split('?', 1)[1])
        return urllib.unquote_plus(params['videoUrl'][0])


class ArchiveVideo(object):
    @staticmethod
    def get_flashvideo_url(src):
        if src.find('http://www.archive.org/flow/flowplayer.commercial-3.2.1.swf') > -1:
            print src.find('http://www.archive.org/flow/flowplayer.commercial-3.2.1.swf')
            return ArchiveVideo.swf_3_21(src)
        elif src.find('http://www.archive.org/flow/flowplayer.commercial-3.0.5.swf') > -1:
            return ArchiveVideo.swf_3_05(src)
        else:
            print 'Unknown swf version for ArchiveVideo.'
        return None

    @staticmethod
    def swf_3_05(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        flashvars = embed_tags.find('embed')['flashvars']
        obj = json.loads(flashvars.split('=', 1)[1].replace("'", '"'))
        path = obj['playlist'][1]['url'] 
        return path

    @staticmethod
    def swf_3_21(src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        flashvars = embed_tags.find('embed')['flashvars']
        obj = json.loads(flashvars.split('=', 1)[1].replace("'", '"'))
        base_url = obj['clip']['baseUrl']
        path = obj['playlist'][1]['url'] 
        return urlparse.urljoin(base_url, path)
