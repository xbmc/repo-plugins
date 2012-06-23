#
#      Copyright (C) 2011 Tommy Winther
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
import os
import simplejson
import time
import urllib
import urllib2

API_URL = 'http://www.dr.dk/NU/api/%s'

class DrNuApi(object):
    def __init__(self, cachePath, cacheMinutes):
        """
        DR NU API specs is available at http://www.dr.dk/nu/api/

        @param self:
        @param cacheMinutes: the contents will be retrieve from the cache if it's age is less than specified minutes
        @type cacheMinutes: int
        """
        self.cachePath = cachePath
        self.cacheMinutes = cacheMinutes

    def getProgramSeries(self, limitToSlugs = None, label = None):
        series = self._call_api('programseries', 'programseries.json')
        if limitToSlugs is not None:
            seriesWithSlug = list()
            for slug in limitToSlugs:
                for serie in series:
                    if slug == serie['slug']:
                        seriesWithSlug.append(serie)
                        
            series = seriesWithSlug

        if label is not None:
            seriesWithLabel = list()
            for serie in series:
                if label.decode('utf-8', 'ignore') in serie['labels']:
                    seriesWithLabel.append(serie)

            series = seriesWithLabel

        return series

    def getProgramSeriesInfo(self, slug):
        series = self.getProgramSeries()
        for serie in series:
            if serie['slug'] == slug:
                return serie

        return None

    def getProgramSeriesLabels(self):
        labels = list()
        series = self.getProgramSeries()
        for serie in series:
            for label in serie['labels']:
                if not label in labels:
                    labels.append(label)

        list.sort(labels)
        return labels


    def getAllVideos(self):
        return self._call_api('videos/all', 'all.json') or list()

    def getNewestVideos(self):
        return self._call_api('videos/newest', 'newest.json') or list()

    def getLastChanceVideos(self):
        return self._call_api('videos/lastchance', 'lastchance.json') or list()

    def getMostViewedVideos(self):
        return self._call_api('videos/mostviewed', 'mostviewed.json') or list()

    def getSpotlightVideos(self):
        return self._call_api('videos/spot', 'spot.json') or list()

    def getHighlightVideos(self):
        return self._call_api('videos/highlight', 'highlight.json') or list()

    def getPremiereVideos(self):
        return self._call_api('videos/premiere', 'premiere.json') or list()

    def getProgramSeriesVideos(self, programSeriesSlug):
        return self._call_api('programseries/%s/videos' % programSeriesSlug, 'programseries-%s.json' % programSeriesSlug) or list()

    def getVideoById(self, id):
        response = self._call_api('videos/%s' % id, 'videobyid-%s.json' % id)
        if type(response) in [str, unicode]:
            print 'Video with ID %s not found' % id
            return None
        else:
            return response

    def search(self, term, limit = 100):
        if not term:
            return list()
        return self._call_api('search/%s?limit=%d' % (urllib.quote(term), limit)) or list()

    def getProgramSeriesImageUrl(self, programSlug, width, height = None):
        if height is None:
            height = width
        return API_URL % ('programseries/%s/images/%dx%d.jpg' % (programSlug, width, height))

    def getVideoImageUrl(self, id, width, height = None):
        if height is None:
            height = width
        return API_URL % ('videos/%s/images/%dx%d.jpg' % (id, width, height))

    def getChapterImageUrl(self, id, width, height = None):
        if height is None:
            height = width
        return API_URL % ('chapters/%s/images/%dx%d.jpg' % (id, width, height))

    def _call_api(self, path, cacheFilename = None):
        print "Calling API: " + API_URL % path

        if cacheFilename:
            cachePath = os.path.join(self.cachePath, cacheFilename)
            try:
                cachedOn = os.path.getmtime(cachePath)
            except OSError: # File not found
                cachedOn = 0

            if not os.path.exists(cachePath) or time.time() - self.cacheMinutes * 60 >= cachedOn:
                # Cache expired or miss
                content = self._http_request(path)

                if content:
                    try:
                        f = open(cachePath, 'w')
                        f.write(content)
                        f.close()
                    except Exception:
                        pass # just too bad if file system is read-only

            else:
                f = open(cachePath)
                content = f.read()
                f.close()

        else:
            content = self._http_request(path)

        if content is not None:
            try:
                return simplejson.loads(content)
            except Exception, ex:
                raise DrNuException(ex)
        else:
            return []

    def _http_request(self, path):
        try:
            u = urllib2.urlopen(API_URL % path)
            content = u.read()
            u.close()
        except Exception as ex:
            raise DrNuException(ex)
        return content


class DrNuException(Exception):
    pass

if __name__ == '__main__':
    api = DrNuApi('/tmp', 0)
#    json =  api.getProgramSeriesVideos('paa-skinner')
    json =  api.getVideoById(16746)
    s = simplejson.dumps(json, sort_keys=True, indent='    ')
    print '\n'.join([l.rstrip() for l in  s.splitlines()])