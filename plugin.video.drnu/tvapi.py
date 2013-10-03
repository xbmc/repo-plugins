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

try:
    import json
except:
    import simplejson as json
import urllib
import urllib2

SLUG_HIGHLIGHTS='hoejdepunkter'
SLUG_SPOTS='test-spotliste'
SLUG_PREMIERES='forpremierer'

class TvApi(object):

    def bundle(self, title=None, bundleType='Series', limit=500, channelType='TV', slugs=None):
        params = {
            'BundleType': '$eq("%s")' % bundleType,
            'ChannelType': '$eq("%s")' % channelType,
            'limit': '$eq(%d)' % limit
        }
        if title:
            params['Title'] = ['$orderby("asc")', '$like("%s")' % title]
        if slugs:
            params['Slug'] = '$in("%s")' % '","'.join(slugs)
        return self._http_request('http://www.dr.dk/mu/bundle', params)

    def bundlesWithPublicAsset(self, title=None, bundleType='Series', limit=5000, channelType='TV'):
        params = {
            'BundleType': '$eq("%s")' % bundleType,
            'Title': ['$orderby("asc")'],
            'ChannelType': '$eq("%s")' % channelType,
            'limit': '$eq(%d)' % limit
        }
        if title:
            params['Title'].append('$like("%s")' % title)
        return self._http_request('http://www.dr.dk/mu/view/bundles-with-public-asset', params)

    def searchBundle(self, text):
        params = {
            'Title': '$like("%s*")' % text
        }
        return self._http_request('http://www.dr.dk/mu/search/bundle', params)

    def getMostViewedProgramCards(self, days=7, count=100, channelType='TV'):
        params = {
            'count': count,
            'days': days,
            'ChannelType': channelType
        }
        return self._http_request('http://www.dr.dk/mu/View/programviews', params)

    def programCard(self, slug):
        try:
            return self._http_request('http://www.dr.dk/mu/programcard/expanded/' + slug)
        except IOError:
            return None

    def programCardRelations(self, relationsSlug, limit=500):
        params = {
            'Relations.Slug': '$eq("%s")' % relationsSlug,
            'limit': '$eq(%d)' % limit
        }
        return self._http_request('http://www.dr.dk/mu/programcard', params)

    def searchProgramCard(self, text):
        params = {
            'Title': '$like("%s*")' % text
        }
        return self._http_request('http://www.dr.dk/mu/search/programcard', params)

    def getAsset(self, kind, programCard):
        if 'ProgramCard' in programCard:
            programCard = programCard['ProgramCard']
        if 'Assets' in programCard:
            for asset in programCard['Assets']:
                if asset['Kind'] == kind:
                    return asset
        return None

    def getLink(self, asset, target = None):
        bitRate = 0
        uri = None
        if 'Links' in asset:
            for link in asset['Links']:
                if (target is None or link['Target'] == target) and ('Bitrate' in link and link['Bitrate'] > bitRate):
                    uri = link['Uri']
                    bitRate = link['Bitrate']
                elif not 'Bitrate' in link and uri is None:
                    uri = link['Uri']
        return uri

    def _http_request(self, url, params=None):
        try:
            if params:
                url = url + '?' + urllib.urlencode(params, doseq=True)

            u = urllib2.urlopen(url, timeout=30)
            content = u.read()
            u.close()

            return json.loads(content)
        except Exception as ex:
            raise TvNuException(ex)


class TvNuException(Exception):
    pass

if __name__ == '__main__':
    api = TvApi()
    print api.programCardRelations('so-ein-ding', limit=50)
