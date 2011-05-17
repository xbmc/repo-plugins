import os
import simplejson
import time
import urllib2

class DrNuApi(object):
    BASE_API_URL = 'http://www.dr.dk/NU/api/%s'

    def __init__(self, cachePath, cacheMinutes):
        """
        DR NU API specs is available at http://www.dr.dk/nu/api/

        @param self:
        @param cacheMinutes: the contents will be retrieve from the cache if it's age is less than specified minutes
        @type cacheMinutes: int
        """
        self.cachePath = cachePath
        self.cacheMinutes = cacheMinutes

    def getProgramSeries(self):
        return self._call_api('programseries', 'programseries.json')

    def getAllVideos(self):
        return self._call_api('videos/all', 'all.json')

    def getNewestVideos(self):
        return self._call_api('videos/newest', 'newest.json')

    def getSpotlightVideos(self):
        return self._call_api('videos/spot', 'spot.json')

    def getProgramSeriesVideos(self, programSeriesSlug):
        return self._call_api('programseries/%s/videos' % programSeriesSlug, 'programseries-%s.json' % programSeriesSlug)

    def getVideoById(self, id):
        return self._call_api('videos/%s' % id, 'videos-%s.json' % id)

    def getProgramSeriesImageUrl(self, programSlug, width, height = None):
        if height is None:
            height = width
        return self.BASE_API_URL % ('programseries/%s/images/%dx%d.jpg' % (programSlug, width, height))

    def getVideoImageUrl(self, id, width, height = None):
        if height is None:
            height = width
        return self.BASE_API_URL % ('videos/%s/images/%dx%d.jpg' % (id, width, height))

    def _call_api(self, path, cacheFilename):
        cachePath = os.path.join(self.cachePath, cacheFilename)
        try:
            cachedOn = os.path.getmtime(cachePath)
        except OSError: # File not found
            cachedOn = 0

        if time.time() - self.cacheMinutes * 60 >= cachedOn:
            # Cache expired or miss
            u = urllib2.urlopen(self.BASE_API_URL % path)
            content = u.read()
            u.close()

            f = open(cachePath, 'w')
            f.write(content)
            f.close()

        else:
            f = open(cachePath)
            content = f.read()
            f.close()

        return simplejson.loads(content)

