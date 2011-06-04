import os
import simplejson
import time
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
                if label in serie['labels']:
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
        return self._call_api('videos/all', 'all.json')

    def getNewestVideos(self):
        return self._call_api('videos/newest', 'newest.json')

    def getMostViewedVideos(self):
        return self._call_api('videos/mostviewed', 'mostviewed.json')

    def getSpotlightVideos(self):
        return self._call_api('videos/spot', 'spot.json')

    def getProgramSeriesVideos(self, programSeriesSlug):
        return self._call_api('programseries/%s/videos' % programSeriesSlug, 'programseries-%s.json' % programSeriesSlug)

    def getVideoById(self, id):
        return self._call_api('videos/%s' % id, 'videobyid-%s.json' % id)

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


    def _call_api(self, path, cacheFilename):
        print "Calling API: " + API_URL % path

        cachePath = os.path.join(self.cachePath, cacheFilename)
        try:
            cachedOn = os.path.getmtime(cachePath)
        except OSError: # File not found
            cachedOn = 0

        if time.time() - self.cacheMinutes * 60 >= cachedOn:
            # Cache expired or miss
            try:
                u = urllib2.urlopen(API_URL % path)
                content = u.read()
                u.close()

                f = open(cachePath, 'w')
                f.write(content)
                f.close()
            except urllib2.HTTPError, ex:
                print "HTTPError: " + str(ex.msg)
                content = None

        else:
            f = open(cachePath)
            content = f.read()
            f.close()

        if content is not None:
            return simplejson.loads(content)
        else:
            return None

if __name__ == '__main__':
    api = DrNuApi('/tmp', 0)
    json =  api.getProgramSeriesLabels()
    s = simplejson.dumps(json, sort_keys=True, indent='    ')
    print '\n'.join([l.rstrip() for l in  s.splitlines()])