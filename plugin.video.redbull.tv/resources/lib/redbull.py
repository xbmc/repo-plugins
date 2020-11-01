# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
""" Implementation of RedBullTV class """

from __future__ import absolute_import, division, unicode_literals
import xbmc
from kodiutils import to_unicode


class RedBullTV():

    REDBULL_STREAMS = 'https://dms.redbull.tv/v3/'
    REDBULL_API = 'https://api.redbull.tv/v3/'
    REDBULL_RESOURCES = 'https://resources.redbull.tv/'

    def __init__(self):
        self.token = self.get_json(self.REDBULL_API + 'session?category=smart_tv&os_family=android', use_token=False)['token']

    def get_play_url(self, uid):
        return self.REDBULL_STREAMS + uid + '/' + self.token + '/playlist.m3u8'

    def get_collection_url(self, uid):
        return self.REDBULL_API + 'collections/' + uid

    def get_product_url(self, uid):
        return self.REDBULL_API + 'products/' + uid

    def get_search_url(self, query):
        return self.REDBULL_API + 'search?q=' + query

    def get_json(self, url, use_token=False):
        try:  # Python 3
            from urllib.error import URLError
            from urllib.request import Request, urlopen
        except ImportError:  # Python 2
            from urllib2 import Request, URLError, urlopen

        request = Request(url)
        if use_token:
            request.add_header('Authorization', self.token)
        try:
            response = urlopen(request)
        except URLError as exc:
            raise IOError(*exc.reason)  # pylint: disable=raise-missing-from

        from json import loads
        xbmc.log('Access: {url}'.format(url=url), xbmc.LOGINFO)
        # NOTE: With Python 3.5 and older json.loads() does not support bytes or bytearray, so we convert to unicode
        return loads(to_unicode(response.read()))

    def get_epg(self):
        return self.get_json(self.REDBULL_API + 'epg?complete=true', use_token=True)

    def get_image_url(self, element_id, resources, element_type, width=1024, quality=70):
        if element_type == 'fanart':
            if 'rbtv_background_landscape' in resources:
                image_type = 'rbtv_background_landscape'
            else:
                return None
        elif element_type == 'landscape':
            if 'rbtv_cover_art_landscape' in resources:
                image_type = 'rbtv_cover_art_landscape'
            elif 'rbtv_display_art_landscape' in resources:
                image_type = 'rbtv_display_art_landscape'
            elif 'rbtv_background_landscape' in resources:
                image_type = 'rbtv_background_landscape'
            else:
                return None
        elif element_type == 'banner':
            if 'rbtv_cover_art_banner' in resources:
                image_type = 'rbtv_cover_art_banner'
            elif 'rbtv_display_art_banner' in resources:
                image_type = 'rbtv_display_art_banner'
            else:
                return None
        elif element_type == 'poster':
            if 'rbtv_cover_art_portrait' in resources:
                image_type = 'rbtv_cover_art_portrait'
            elif 'rbtv_display_art_portrait' in resources:
                image_type = 'rbtv_display_art_portrait'
            else:
                return None
        else:
            return None

        return '{base}/{id}/{type}/im:i:w_{width},q_{quality}'.format(base=self.REDBULL_RESOURCES, id=element_id, type=image_type, width=width, quality=quality)

    def get_content(self, url=None, page=1, limit=20):
        return self.get_json(url + ('?', '&')['?' in url] + 'limit=' + str(limit) + '&offset=' + str((page - 1) * limit), use_token=True)
