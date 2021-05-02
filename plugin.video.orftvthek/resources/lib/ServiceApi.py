#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import time
import sys

PY3 = sys.version_info.major >=3
if PY3:
    from urllib.error import HTTPError
else:
    from urllib2 import HTTPError

from .Base import *
from .Scraper import *


class serviceAPI(Scraper):
    __urlBase = 'https://api-tvthek.orf.at/api/v3/'
    __urlLive = 'livestreams/24hours?limit=20'
    __urlMostViewed = 'page/startpage'
    __urlNewest = 'page/startpage/newest'
    __urlSearch = __urlBase + 'search/%s?limit=1000'
    __urlShows = 'profiles?limit=1000'
    __urlTips = 'page/startpage/tips'
    __urlTopics = 'topics/overview?limit=1000'

    serviceAPIEpisode = 'episode/%s'
    serviceAPIDate = 'schedule/%s?limit=1000'
    serviceAPIDateFrom = 'schedule/%s/%d?limit=1000'
    serviceAPIProgram = 'profile/%s/episodes'
    servieAPITopic = 'topic/%s'
    serviceAPITrailers = 'page/preview?limit=100'
    serviceAPIHighlights = 'page/startpage'

    httpauth = 'cHNfYW5kcm9pZF92Mzo2YTYzZDRkYTI5YzcyMWQ0YTk4NmZkZDMxZWRjOWU0MQ=='

    def __init__(self, xbmc, settings, pluginhandle, quality, protocol, delivery, defaultbanner, defaultbackdrop, usePlayAllPlaylist):
        self.translation = settings.getLocalizedString
        self.xbmc = xbmc
        self.videoQuality = quality
        self.videoDelivery = delivery
        self.videoProtocol = protocol
        self.pluginhandle = pluginhandle
        self.defaultbanner = defaultbanner
        self.defaultbackdrop = defaultbackdrop
        self.usePlayAllPlaylist = usePlayAllPlaylist
        debugLog('ServiceAPI  - Init done', xbmc.LOGDEBUG)

    def getHighlights(self):
        try:
            response = self.__makeRequest(self.serviceAPIHighlights)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for result in json.loads(response.read().decode('UTF-8')).get('highlight_teasers'):
                if result.get('target').get('model') == 'Segment':
                    self.JSONSegment2ListItem(result.get('target'))

    def getMostViewed(self):
        try:
            response = self.__makeRequest(self.__urlMostViewed)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for result in json.loads(response.read().decode('UTF-8')).get('most_viewed_segments'):
                if result.get('model') == 'Segment':
                    self.JSONSegment2ListItem(result)

    def getNewest(self):
        self.getTableResults(self.__urlNewest)

    def getTips(self):
        self.getTableResults(self.__urlTips)

    def getFocus(self):
        debugLog('"In Focus" not available', level=xbmc.LOGDEBUG)

    def getTableResults(self, urlAPI):
        try:
            response = self.__makeRequest(urlAPI)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for result in json.loads(response.read().decode('UTF-8')):
                if result.get('model') == 'Episode':
                    self.__JSONEpisode2ListItem(result)
                elif result.get('model') == 'Tip':
                    self.__JSONVideoItem2ListItem(result.get('_embedded').get('video_item'))

        else:
            debugLog('ServiceAPI not available ... switch back to HTML Parsing in the Addon Settings', level=xbmc.LOGDEBUG)
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    # Useful  Methods for JSON Parsing
    def JSONSegment2ListItem(self, JSONSegment):
        if JSONSegment.get('killdate') is not None and time.strptime(JSONSegment.get('killdate')[0:19], '%Y-%m-%dT%H:%M:%S') < time.localtime():
            return
        title = JSONSegment.get('title').encode('UTF-8')
        image = self.JSONImage(JSONSegment.get('_embedded').get('image'))
        description = JSONSegment.get('description')
        duration = JSONSegment.get('duration_seconds')
        date = time.strptime(JSONSegment.get('episode_date')[0:19], '%Y-%m-%dT%H:%M:%S')
        streamingURL = self.JSONStreamingURL(JSONSegment.get('sources'))
        subtitles = [x.get('src') for x in JSONSegment.get('playlist').get('subtitles')]
        return [streamingURL, createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, True, False, self.defaultbackdrop, self.pluginhandle, subtitles)]

    @staticmethod
    def JSONImage(jsonImages, name='image_full'):
        return jsonImages.get('public_urls').get('highlight_teaser').get('url')

    def JSONStreamingURL(self, jsonVideos):
        source = None
        if jsonVideos.get('progressive_download') is not None:
            for streamingUrl in jsonVideos.get('progressive_download'):
                if streamingUrl.get('quality_key') == self.videoQuality:
                    return generateAddonVideoUrl(streamingUrl.get('src'))
                source = streamingUrl.get('src')

        for streamingUrl in jsonVideos.get('hls'):
            if streamingUrl.get('quality_key') == self.videoQuality:
                return generateAddonVideoUrl(streamingUrl.get('src'))
            source = streamingUrl.get('src')
        if source is not None:
            return generateAddonVideoUrl(source)
        else:
            showDialog(self.translation(30014).encode('UTF-8'), self.translation(30050).encode('UTF-8'))
            return

    # list all Categories
    def getCategories(self):
        try:
            response = self.__makeRequest(self.__urlShows)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for result in json.loads(response.read().decode('UTF-8')).get('_embedded').get('items'):
                self.__JSONProfile2ListItem(result)
        else:
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    # list all Episodes for the given Date
    def getDate(self, date, dateFrom=None):
        if dateFrom is None:
            url = self.serviceAPIDate % date
        else:
            url = self.serviceAPIDateFrom % (date, 7)
        response = self.__makeRequest(url)

        episodes = json.loads(response.read().decode('UTF-8')).get('_embedded').get('items')
        if dateFrom is not None:
            episodes = reversed(episodes)

        for episode in episodes:
            self.__JSONEpisode2ListItem(episode)

    # list all Entries for the given Topic
    def getTopic(self, topicID):
        response = self.__makeRequest(self.servieAPITopic % topicID)
        for entrie in json.loads(response.read().decode('UTF-8')).get('_embedded').get('video_items'):
            self.__JSONVideoItem2ListItem(entrie)

    # list all Episodes for the given Broadcast
    def getProgram(self, programID, playlist):
        response = self.__makeRequest(self.serviceAPIProgram % programID)
        responseCode = response.getcode()

        if responseCode == 200:
            episodes = json.loads(response.read().decode('UTF-8')).get('_embedded').get('items')
            if len(episodes) == 1:
                for episode in episodes:
                    self.getEpisode(episode.get('id'), playlist)
                    return

            for episode in episodes:
                self.__JSONEpisode2ListItem(episode, 'teaser')
        else:
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    # listst all Segments for the Episode with the given episodeID
    # If the Episode only contains one Segment, that get played instantly.
    def getEpisode(self, episodeID, playlist):
        playlist.clear()

        response = self.__makeRequest(self.serviceAPIEpisode % episodeID)
        result = json.loads(response.read().decode('UTF-8'))

        if len(result.get('_embedded').get('segments')) == 1:
            listItem = self.JSONSegment2ListItem(result.get('_embedded').get('segments')[0])
            playlist.add(listItem[0], listItem[1])
        else:
            gapless_name = '-- %s --' % self.translation(30059)
            streamingURL = self.JSONStreamingURL(result.get('sources'))
            description = result.get('description')
            duration = result.get('duration_seconds')
            teaser_image = result.get('playlist').get('preview_image_url')
            date = time.strptime(result.get('date')[0:19], '%Y-%m-%dT%H:%M:%S')
            if result.get('playlist').get('is_gapless'):
                subtitles = [x.get('src') for x in result.get('playlist').get('gapless_video').get('subtitles')]
                createListItem(gapless_name, teaser_image, description, duration, time.strftime('%Y-%m-%d', date), '', streamingURL, True, False, self.defaultbackdrop, self.pluginhandle, subtitles)

            if self.usePlayAllPlaylist:
                play_all_name = '-- %s --' % self.translation(30060)
                stream_infos = {
                    'teaser_image': teaser_image,
                    'description': description
                }
                createPlayAllItem(play_all_name, self.pluginhandle, stream_infos)

            for segment in result.get('_embedded').get('segments'):
                listItem = self.JSONSegment2ListItem(segment)
                playlist.add(listItem[0], listItem[1])

    # Parses the Topic Overview Page
    def getThemen(self):
        try:
            response = self.__makeRequest(self.__urlTopics)
            responseCode = response.getcode()
        except ValueError as error:
            responseCode = 404
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for topic in json.loads(response.read().decode('UTF-8')).get('_embedded').get('items'):
                title = topic.get('title').encode('UTF-8')
                description = topic.get('description')
                link = topic.get('id')
                addDirectory(title, None, self.defaultbackdrop, description, link, 'openTopic', self.pluginhandle)

        else:
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    # list all Trailers for further airings
    def getTrailers(self):
        try:
            response = self.__makeRequest(self.serviceAPITrailers)
            responseCode = response.getcode()
        except ValueError as error:
            responseCode = 404
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            for episode in json.loads(response.read().decode('UTF-8'))['_embedded']['items']:
                self.__JSONEpisode2ListItem(episode)
        else:
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    def getArchiv(self):
        pass

    # lists schedule overview (date listing)
    def getSchedule(self):
        for x in range(9):
            date = datetime.datetime.now() - datetime.timedelta(days=x)
            title = '%s' % (date.strftime('%A, %d.%m.%Y'))
            parameters = {'mode': 'openDate', 'link': date.strftime('%Y-%m-%d')}
            if x == 8:
                title = '$s %s' % (self.translation(30064), title)
                parameters = {'mode': 'openDate', 'link': date.strftime('%Y-%m-%d'), 'from': (date - datetime.timedelta(days=150)).strftime('%Y-%m-%d')}
            u = build_kodi_url(parameters)
            createListItem(title, None, None, None, date.strftime('%Y-%m-%d'), '', u, False, True, self.defaultbackdrop, self.pluginhandle)

    # Returns Live Stream Listing
    def getLiveStreams(self):
        try:
            response = self.__makeRequest(self.__urlLive)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            try:
                xbmcaddon.Addon('inputstream.adaptive')
                inputstreamAdaptive = True
            except RuntimeError:
                inputstreamAdaptive = False

            foundProgram = []
            showFullSchedule = xbmcaddon.Addon().getSetting('showLiveStreamSchedule') == 'true'

            for result in json.loads(response.read().decode('UTF-8')).get('_embedded').get('items'):
                description = result.get('description')
                programName = result.get('_embedded').get('channel').get('name')
                livestreamStart = time.strptime(result.get('start')[0:19], '%Y-%m-%dT%H:%M:%S')
                livestreamEnd = time.strptime(result.get('end')[0:19], '%Y-%m-%dT%H:%M:%S')
                duration = max(time.mktime(livestreamEnd) - max(time.mktime(livestreamStart), time.mktime(time.localtime())), 1)
                contextMenuItems = []

                if programName not in foundProgram or showFullSchedule:
                    foundProgram.append(programName)

                    link = self.JSONStreamingURL(result.get('sources'))
                    if inputstreamAdaptive and result.get('restart'):
                        contextMenuItems.append((self.translation(30063), 'RunPlugin(plugin://%s/?mode=liveStreamRestart&link=%s)' % (xbmcaddon.Addon().getAddonInfo('id'), result.get('id'))))

                    title = "[%s] %s %s (%s)" % (programName, self.translation(30063) if inputstreamAdaptive and result.get('restart') else '', result.get('title'), time.strftime('%H:%M', livestreamStart))

                    banner = self.JSONImage(result.get('_embedded').get('image'))

                    createListItem(title, banner, description, duration, time.strftime('%Y-%m-%d', livestreamStart), programName, link, True, False, self.defaultbackdrop, self.pluginhandle,
                                   contextMenuItems=contextMenuItems)
        else:
            showDialog(self.translation(30045).encode('UTF-8'), self.translation(30046).encode('UTF-8'))

    def liveStreamRestart(self, link):
        try:
            xbmcaddon.Addon('inputstream.adaptive')
        except RuntimeError:
            return

        try:
            response = self.__makeRequest('livestream/' + link)
            responseCode = response.getcode()
        except HTTPError as error:
            responseCode = error.getcode()

        if responseCode == 200:
            result = json.loads(response.read().decode('UTF-8'))

            title = result.get('title').encode('UTF-8')
            image = self.JSONImage(result.get('_embedded').get('image'))
            description = result.get('description')
            duration = result.get('duration_seconds')
            date = time.strptime(result.get('start')[0:19], '%Y-%m-%dT%H:%M:%S')

            ApiKey = '2e9f11608ede41f1826488f1e23c4a8d'
            bitmovinStreamId = result.get('_embedded').get('channel').get('restart_urls').get('default')
            if bitmovinStreamId:
                bitmovinStreamId = bitmovinStreamId.replace("https://playerapi-restarttv.ors.at/livestreams/", "").replace("/sections/", "")
                bitmovinStreamId = bitmovinStreamId.split("?")[0]
            response = url_get_request('https://playerapi-restarttv.ors.at/livestreams/%s/sections/?state=active&X-Api-Key=%s' % (bitmovinStreamId, ApiKey))  # nosec
            section = json.loads(response.read().decode('UTF-8'))[0]

            streamingURL = 'https://playerapi-restarttv.ors.at/livestreams/%s/sections/%s/manifests/hls/?startTime=%s&X-Api-Key=%s' % (bitmovinStreamId, section.get('id'), section.get('metaData').get('timestamp'), ApiKey)

            listItem = createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), result.get('_embedded').get('channel').get('name'), streamingURL, True, False, self.defaultbackdrop,
                                      self.pluginhandle)
            listItem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            listItem.setProperty('inputstream.adaptive.manifest_type', 'hls')
            self.xbmc.Player().play(streamingURL, listItem)

    def __makeRequest(self, url):
        return url_get_request(self.__urlBase + url, self.httpauth)

    def __JSONEpisode2ListItem(self, JSONEpisode, ignoreEpisodeType=None):
        if JSONEpisode.get('killdate') is not None and time.strptime(JSONEpisode.get('killdate')[0:19], '%Y-%m-%dT%H:%M:%S') < time.localtime():
            return

        # Direcotory should be set to False, that the Duration is shown, but then there is an error with the Pluginhandle
        createListItem(
            JSONEpisode.get('title'),
            self.JSONImage(JSONEpisode.get('_embedded').get('image')),
            JSONEpisode.get('description'),
            JSONEpisode.get('duration_seconds'),
            time.strftime('%Y-%m-%d', time.strptime(JSONEpisode.get('date')[0:19], '%Y-%m-%dT%H:%M:%S')),
            JSONEpisode.get('_embedded').get('channel').get('name') if JSONEpisode.get('_embedded').get('channel') is not None else None,
            build_kodi_url({'mode': 'openEpisode', 'link': JSONEpisode.get('id')}),
            False,
            True,
            self.defaultbackdrop,
            self.pluginhandle,
        )

    def __JSONProfile2ListItem(self, jsonProfile):
        createListItem(
            jsonProfile.get('title'),
            self.JSONImage(jsonProfile.get('_embedded').get('image')),
            jsonProfile.get('description'),
            None,
            None,
            None,
            build_kodi_url({'mode': 'openProgram', 'link': jsonProfile.get('id')}),
            False,
            True,
            self.defaultbackdrop,
            self.pluginhandle
        )

    def __JSONVideoItem2ListItem(self, jsonVideoItem):
        if jsonVideoItem.get('_embedded').get('episode') is not None:
            self.__JSONEpisode2ListItem(jsonVideoItem.get('_embedded').get('episode'))
        elif jsonVideoItem.get('_embedded').get('segment') is not None:
            self.JSONSegment2ListItem(jsonVideoItem.get('_embedded').get('segment'))
