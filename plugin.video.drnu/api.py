import os
import simplejson as json

import danishaddons
import danishaddons.web

BASE_API_URL = 'http://www.dr.dk/NU/api/%s'

class DRnuApi(object):
    """
    DR NU API specs is available at http://www.dr.dk/nu/api/

	Keyword arguments:
	cacheMinutes -- the contents will be retrieve from the cache if it's age is less than specified minutes

    """
    def __init__(self, cacheMinutes):
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
        video = danishaddons.web.downloadUrl(BASE_API_URL % ('videos/%s' % id))
        return json.loads(video)

    def getProgramSeriesImageUrl(self, programSlug, width, height = None):
        if height is None:
            height = width
        return BASE_API_URL % ('programseries/%s/images/%dx%d.jpg' % (programSlug, width, height))

    def getVideoImageUrl(self, id, width, height = None):
        if height is None:
            height = width
        return BASE_API_URL % ('videos/%s/images/%dx%d.jpg' % (id, width, height))

    def _call_api(self, path, cacheFilename):
        response = danishaddons.web.downloadAndCacheUrl(
                BASE_API_URL % path,
                os.path.join(danishaddons.ADDON_DATA_PATH, cacheFilename), self.cacheMinutes)
        return json.loads(response)
