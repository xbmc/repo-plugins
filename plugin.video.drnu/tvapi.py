#
#      Copyright (C) 2014 Tommy Winther
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
import hashlib
import os
import datetime
import re
SLUG_PREMIERES='forpremierer'


class Api(object):
    API_URL = 'http://www.dr.dk/mu-online/api/1.2'

    def __init__(self, cachePath):
        self.cachePath = cachePath

    def getLiveTV(self):
        return self._http_request('/channel/all-active-dr-tv-channels')

    def getChildrenFrontItems(self, channel):
        childrenFront = self._http_request('/page/tv/children/front/%s' % channel)
        return self._handle_paging(childrenFront['Programs'])

    def getThemes(self):
        themes = self._http_request('/list/view/themesoverview')
        return themes['Items']

    def getLatestPrograms(self):
        result = self._http_request('/page/tv/programs', {
            'index': '*',
            'orderBy': 'LastPrimaryBroadcastWithPublicAsset',
            'orderDescending': 'true'
        }, cacheMinutes=5)
        return result['Programs']['Items']

    def getProgramIndexes(self):
        result = self._http_request('/page/tv/programs')
        if 'Indexes' in result:
            indexes = result['Indexes']
            for programIndex in indexes:
                programIndex['_Param'] = programIndex['Source'][programIndex['Source'].rindex('/') + 1:]
            return indexes

        return []

    def getSeries(self, query):
        result = self._http_request('/search/tv/programcards-latest-episode-with-asset/series-title-starts-with/%s' % query,
                                    {'limit': 75})
        return self._handle_paging(result)

    def searchSeries(self, query):
        # Remove various characters that makes the API puke
        result = self._http_request('/search/tv/programcards-latest-episode-with-asset/series-title/%s' % re.sub('[&()"\'\.!]', '', query))
        return self._handle_paging(result)

    def getEpisodes(self, slug):
        result = self._http_request('/list/%s' % slug,
                                    {'limit': 48,
                                     'expanded': True})
        return self._handle_paging(result)

    def getEpisode(self, slug):
        return self._http_request('/programcard/%s' % slug)

    def getMostViewed(self):
        result = self._http_request('/list/view/mostviewed',
                                    {'limit': 48})
        return result['Items']

    def getSelectedList(self):
        result = self._http_request('/list/view/selectedlist',
                                    {'limit': 60})
        return result['Items']

    def getVideoUrl(self, assetUri):
        result = self._http_request(assetUri)

        uri = None
        for link in result['Links']:
            if link['Target'] == 'HLS':
                uri = link['Uri']
                break

        subtitlesUri = None
        if 'SubtitlesList' in result and len(result['SubtitlesList']) > 0:
            subtitlesUri = result['SubtitlesList'][0]['Uri']

        return {
            'Uri': uri,
            'SubtitlesUri': subtitlesUri
        }

    def _handle_paging(self, result):
        items = result['Items']
        while 'Next' in result['Paging']:
            result = self._http_request(result['Paging']['Next'])
            items.extend(result['Items'])
        return items

    def _http_request(self, url, params=None, cacheMinutes = 720):
        try:
            if not url.startswith(('http://','https://')):
                url = self.API_URL + urllib.quote(url, '/')

            if params:
                url = url + '?' + urllib.urlencode(params, doseq=True)

            try:
                print url
            except:
                pass

            urlCachePath = os.path.join(self.cachePath, hashlib.md5(url).hexdigest() + '.cache')

            cacheUntil = datetime.datetime.now() - datetime.timedelta(minutes=cacheMinutes)
            if not os.path.exists(urlCachePath) or datetime.datetime.fromtimestamp(os.path.getmtime(urlCachePath)) < cacheUntil:
                u = urllib2.urlopen(url, timeout=30)
                content = u.read()
                u.close()

                try:
                    f = open(urlCachePath, 'w')
                    f.write(content)
                    f.close()
                except:
                    pass # ignore, cache has no effect
            else:
                f = open(urlCachePath)
                content = f.read()
                f.close()

            return json.loads(content)
        except Exception as ex:
            raise ApiException(ex)


class ApiException(Exception):
    pass

if __name__ == '__main__':
    api = Api()
    print api.programCardRelations('so-ein-ding', limit=50)
