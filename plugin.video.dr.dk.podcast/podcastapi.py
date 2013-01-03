#
#      Copyright (C) 2012 Tommy Winther
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
import urllib
import urllib2

API_URL = 'http://www.dr.dk/podcast/api/%s'

# http://www.dr.dk/podcast/api/getchannels

# http://www.dr.dk/podcast/api/GetByFirst?letter=&take=18
# http://www.dr.dk/podcast/api/GetByFirst?letter=d&take=18&skip=18
# http://www.dr.dk/podcast/api/GetByFirst?letter=&channel=dr%20hd&take=undefined

# http://www.dr.dk/podcast/api/search?query=ding&take=18
# http://www.dr.dk/podcast/api/search?query=ding&channel=dr1&take=undefined

TYPE_RADIO = 'radio'
TYPE_TV = 'tv'

class PodcastApi(object):
    def __init__(self, type):
        self.type = type

    def getChannels(self):
        return self._call_api('getchannels')

    def getByFirstLetter(self, letter, start = None, count = 1000, channel = None):
        params = {'letter' : letter}
        if count:
            params['take'] = count
        if start:
            params['skip'] = start
        if channel:
            params['channel'] = channel.encode('iso-8859-1')

        return self._call_api('GetByFirst', params)

    def search(self, query = None, start = None, count = 1000, channel = None):
        params = dict()
        if query:
            params['query'] = query
        if count:
            params['take'] = count
        if start:
            params['skip'] = start
        if channel:
            params['channel'] = channel.encode('iso-8859-1')

        return self._call_api('search', params)

    def _call_api(self, method, params = None):
        url = API_URL % method

        if params:
            params.update({'type' : self.type})
            url += '?' + urllib.urlencode(params)

        print "Calling API: " + url

        content = self._http_request(url)

        if content is not None:
            try:
                return simplejson.loads(content)
            except Exception, ex:
                raise PodcastException(ex)
        else:
            return []

    def _http_request(self, url):
        try:
            u = urllib2.urlopen(url, timeout = 30)
            content = u.read()
            u.close()
        except Exception as ex:
            raise PodcastException(ex)
        return content


class PodcastException(Exception):
    pass

if __name__ == '__main__':
    api = PodcastApi(TYPE_TV)
    json =  api.getChannels()
    s = simplejson.dumps(json, sort_keys=True, indent='    ')
    print '\n'.join([l.rstrip() for l in  s.splitlines()])