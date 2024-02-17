from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor


class ComedyCentralIE(MTVServicesInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cc\.com/(?:episodes|video(?:-clips)?|collection-playlist)/(?P<id>[0-9a-z]{6})'
    _FEED_URL = 'http://comedycentral.com/feeds/mrss/'
    _MGID = False


class ComedyCentralMgidIE(ComedyCentralIE):
    _VALID_URL = r'mgid:arc:(?:video|episode|promo):comedycentral.com:(?P<id>[a-z\d]{8}-[a-z\d]{4}-[a-z\d]{4}-[a-z\d]{4}-[a-z\d]{12})'
    _MGID = True
