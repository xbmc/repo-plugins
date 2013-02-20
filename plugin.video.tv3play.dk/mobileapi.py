#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import simplejson
import urllib2
import urllib

IPAD_USERAGENT = 'Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.0.2 Mobile/9A5248d Safari/6533.18.5'

API_URL = ' http://www.%s/mobileapi/%s'
IMAGE_URL = 'http://play.pdl.viaplay.com/%s'
VIASTREAM_URL = 'http://viastream.viasat.tv/%s'

class TV3PlayMobileApi(object):
    def __init__(self, region):
        self.region = region

    def getAllFormats(self):
        formats = list()

        format = self.format()
        for section in format['sections']:
            formats.extend(section['formats'])

        return formats

    def getVideos(self, category):
        return self._call_api('formatcategory/%s/video' % category) #?splitByType' % category)

    def getMobileStream(self, videoId):
        return self._call_api(VIASTREAM_URL % ('MobileStream/%s' % videoId))

    def getMobileData(self, videoId):
        return self._call_api(VIASTREAM_URL % ('MobileData/%s' % videoId))

    def format(self):
        """
        :rtype : dict
        """
        return self._call_api('format')

    def detailed(self, formatId):
        return self._call_api('detailed', {'formatid' : formatId})

    def featured(self):
        return self._call_api('featured')

    def mostviewed(self):
        return self._call_api('mostviewed')


    def _call_api(self, url, params = None):
        if url[0:4] != 'http':
            url = API_URL % (self.region, url)

        if params:
            url += '?' + urllib.urlencode(params)

        print "Calling API: " + url

        content = self._http_request(url)

        if content is not None and content != '':
            try:
                return simplejson.loads(content)
            except Exception, ex:
                raise TV3PlayMobileApiException(ex)
        else:
            return []

    def _http_request(self, url):
        try:
            r = urllib2.Request(url, headers = {
                'user-agent' : IPAD_USERAGENT
            })
            u = urllib2.urlopen(r)
            content = u.read()
            u.close()
        except Exception as ex:
            raise TV3PlayMobileApiException(ex)
        return content


class TV3PlayMobileApiException(Exception):
    pass


if __name__ == '__main__':
    api = TV3PlayMobileApi('tv3play.dk')
    print api.featured()
