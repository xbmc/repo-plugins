#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import time
import sys
import re

PY3 = sys.version_info.major >=3
if PY3:
    from urllib.error import HTTPError
else:
    from urllib2 import HTTPError

from .Base import *
from .Scraper import *


class serviceAPI(Scraper):
    __urlBase = 'https://api-tvthek.orf.at/api/v3/'
    __urlBaseV4 = 'https://api-tvthek.orf.at/api/v4.2/'
    __urlLive = 'livestreams/24hours?limit=20'
    __urlLiveChannels = 'livestreams'
    __urlMostViewed = 'page/startpage'
    __urlNewest = 'page/startpage/newest'
    __urlSearch = __urlBase + 'search/%s?limit=1000'
    __urlShows = 'profiles?limit=1000'
    __urlTips = 'page/startpage/tips'
    __urlTopics = 'topics/overview?limit=1000'
    __urlChannel = 'channel/'
    __urlDRMLic = 'https://drm.ors.at/acquire-license/widevine'
    __brandIdDRM = '13f2e056-53fe-4469-ba6d-999970dbe549'
    __bundeslandMap = {
        'orf2b': 'Burgenland',
        'orf2stmk': 'Steiermark',
        'orf2w': 'Wien',
        'orf2ooe': 'Oberösterreich',
        'orf2k': 'Kärnten',
        'orf2n': 'Niederösterreich',
        'orf2s': 'Salzburg',
        'orf2v': 'Vorarlberg',
        'orf2t': 'Tirol',
    }
    __channelMap = {
        'orf1': 'ORF 1',
        'orf2': 'ORF 2',
        'orf3': 'ORF III',
        'orfs': 'ORF Sport+',
        'live_special': 'Special'
    }

    serviceAPIEpisode = 'episode/%s'
    serviceAPIDate = 'schedule/%s?limit=1000'
    serviceAPIDateFrom = 'schedule/%s/%d?limit=1000'
    serviceAPIProgram = 'profile/%s/episodes'
    servieAPITopic = 'topic/%s'
    serviceAPITrailers = 'page/preview?limit=100'
    serviceAPIHighlights = 'page/startpage'

    httpauth = 'cHNfYW5kcm9pZF92M19uZXc6MDY1MmU0NjZkMTk5MGQxZmRmNDBkYTA4ZTc5MzNlMDY=='

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

    def getLivestreamByChannel(self, channel):
        response = self.__makeRequestV4(self.__urlLiveChannels)
        response_raw = response.read().decode('UTF-8')
        channels = json.loads(response_raw)

        live_link = False
        for result in channels:
            if channel in self.__bundeslandMap:
                channel_items =  channels[result].get('items')
                for channel_item in channel_items:
                    if channel_item.get('title') == "%s heute" % self.__bundeslandMap[channel]:
                        live_link = channel_item.get('_links').get('self').get('href')
            if result == channel or channel in self.__bundeslandMap and result == channel[0:4] and not live_link:
                live_link = channels[result].get('items')[0].get('_links').get('self').get('href')

        if live_link:
            response = url_get_request(live_link, self.httpauth)
            response_raw = response.read().decode('UTF-8')
            live_json = json.loads(response_raw)
            if live_json.get('is_drm_protected'):
                video_url = self.JSONStreamingDrmURL(live_json)
                uhd_25_video_url = self.JSONStreamingDrmURL(live_json, 'uhdbrowser')
                if uhd_25_video_url:
                    video_url = uhd_25_video_url;
                uhd_50_video_url = self.JSONStreamingDrmURL(live_json, 'uhdsmarttv')
                if uhd_50_video_url:
                    video_url = uhd_50_video_url
                license_url = self.JSONLicenseDrmURL(live_json)
                return {'title': live_json.get('title'), 'description': live_json.get('share_subject'), 'url': video_url,'license': license_url}
            else:
                video_url = self.JSONStreamingURL(live_json.get('sources'))
                return {'title': live_json.get('title'), 'description': live_json.get('share_subject'), 'url': video_url}

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
            debugLog('ServiceAPI not available for %s ... switch back to HTML Parsing in the Addon Settings' % urlAPI, level=xbmc.LOGDEBUG)
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
                # Remove Get Parameters because InputStream Adaptive cant handle it.
                source = re.sub(r"\?[\S]+", '', streamingUrl.get('src'), 0)
                return generateAddonVideoUrl(source)
            source = re.sub(r"\?[\S]+", '', streamingUrl.get('src'), 0)
        if source is not None:
            return generateAddonVideoUrl(source)
        else:
            showDialog(self.translation(30014).encode('UTF-8'), self.translation(30050).encode('UTF-8'))
            return

    def JSONLicenseDrmURL(self, jsonData):
        if jsonData.get('drm_token') is not None:
            token = jsonData.get('drm_token')
            license_url = "%s?BrandGuid=%s&userToken=%s" % (self.__urlDRMLic, self.__brandIdDRM, token)
            debugLog("DRM License Url %s" % license_url)
            return license_url

    def JSONStreamingDrmURL(self, jsonData, uhd_profile = False):
        if jsonData.get('drm_token') is not None:
            license_url = self.JSONLicenseDrmURL(jsonData)
            jsonVideos = jsonData.get('sources')

            if uhd_profile:
                for streamingUrl in jsonVideos.get('dash'):
                    if streamingUrl.get('is_uhd') and streamingUrl.get('quality_key').lower() == uhd_profile:
                        source = re.sub(r"\?[\S]+", '', streamingUrl.get('src'), 0)
                        return generateDRMVideoUrl(source, license_url)
                return False

            for streamingUrl in jsonVideos.get('dash'):
                if streamingUrl.get('quality_key').lower()[0:3] == self.videoQuality:
                    return generateDRMVideoUrl(streamingUrl.get('src'), license_url)
                source = streamingUrl.get('src')
                # Remove Get Parameters because InputStream Adaptive cant handle it.
                source = re.sub(r"\?[\S]+", '', source, 0)
            if source is not None:
                return generateDRMVideoUrl(source, license_url)
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
                title = '%s %s' % (self.translation(30064), title)
                parameters = {'mode': 'openDate', 'link': date.strftime('%Y-%m-%d'), 'from': (date - datetime.timedelta(days=150)).strftime('%Y-%m-%d')}
            u = build_kodi_url(parameters)
            createListItem(title, None, None, None, date.strftime('%Y-%m-%d'), '', u, False, True, self.defaultbackdrop, self.pluginhandle)

    # Fetch stream details.
    def getStreamInfos(self, item, inputstreamAdaptive):
        infos = {}
        live_link = item.get('_links').get('self').get('href')
        response = url_get_request(live_link, self.httpauth)
        response_raw = response.read().decode('UTF-8')
        infos['live'] = json.loads(response_raw)
        infos['drmurl'] = self.JSONLicenseDrmURL(infos['live'])
        if inputstreamAdaptive and infos['live'].get('is_drm_protected'):
            infos['stream'] = self.JSONStreamingDrmURL(infos['live'])
        else:
            infos['stream'] = self.JSONStreamingURL(infos['live'].get('sources'))

        infos['uhd25_stream'] = self.JSONStreamingDrmURL(infos['live'], 'uhdbrowser')
        infos['uhd50_stream'] = self.JSONStreamingDrmURL(infos['live'], 'uhdsmarttv')
        infos['items'] = {}
        return infos

    # Builds a livestream item.
    def buildStreamItem(self, item, channel, stream_imfo, inputstreamAdaptive, use_restart=True):
        description = item.get('description')
        title = item.get('title')
        programName = channel
        if channel in self.__channelMap:
            programName = self.__channelMap[channel]
        livestreamStart = time.strptime(item.get('start')[0:19], '%Y-%m-%dT%H:%M:%S')
        livestreamEnd = time.strptime(item.get('end')[0:19], '%Y-%m-%dT%H:%M:%S')
        duration = max(time.mktime(livestreamEnd) - max(time.mktime(livestreamStart), time.mktime(time.localtime())), 1)
        contextMenuItems = []
        restart_url = False
        if inputstreamAdaptive and item.get('restart'):
            restart_parameters = {"mode": "liveStreamRestart", "link": item.get('id'), "lic_url": stream_imfo['drmurl']}
            restart_url = build_kodi_url(restart_parameters)
            contextMenuItems.append((self.translation(30063), 'RunPlugin(%s)' % restart_url))

        banner = self.JSONImage(item.get('_embedded').get('image'))
        item_title = "[%s] %s %s (%s)" % (programName, "[%s]" % self.translation(30063) if inputstreamAdaptive and restart_url else '', title, time.strftime('%H:%M', livestreamStart))
        if item.get('uhd') and stream_imfo['uhd25_stream']:
            createListItem("[UHD] %s" % item_title, banner, description, duration,time.strftime('%Y-%m-%d', livestreamStart), programName, stream_imfo['uhd25_stream'], True, False, self.defaultbackdrop, self.pluginhandle)
        if item.get('uhd') and stream_imfo['uhd50_stream']:
            createListItem("[UHD 50fps] %s" % item_title, banner, description, duration,time.strftime('%Y-%m-%d', livestreamStart), programName, stream_imfo['uhd50_stream'], True, False, self.defaultbackdrop, self.pluginhandle)

        createListItem(item_title, banner, description, duration, time.strftime('%Y-%m-%d', livestreamStart), programName, stream_imfo['stream'], True, False, self.defaultbackdrop, self.pluginhandle, contextMenuItems=contextMenuItems)

    # Returns Live Stream Listing
    def getLiveStreams(self):
        try:
            xbmcaddon.Addon('inputstream.adaptive')
            inputstreamAdaptive = True
        except RuntimeError:
            inputstreamAdaptive = False

        showFullSchedule = xbmcaddon.Addon().getSetting('showLiveStreamSchedule') == 'true'

        response = self.__makeRequestV4(self.__urlLiveChannels)
        response_raw = response.read().decode('UTF-8')
        channels = json.loads(response_raw)
        channelresults = {}

        # Prefetch the stream infos to limit request for each stream.
        for channel in channels:
            channelresults[channel] = {}
            channel_items =  channels[channel].get('items')
            for channel_item in channel_items:
                channelresults[channel] = self.getStreamInfos(channel_item, inputstreamAdaptive)
                channelresults[channel]['items'] = channel_items
                break

        # Render current streams first.
        for channel in channels:
            for upcoming in channelresults[channel]['items']:
                if not 'upcoming' in channels[channel] or ('upcoming' in channels[channel] and upcoming.get('start')[0:17] == channels[channel]['upcoming'].get('start')[0:17]):
                    if not 'upcoming' in channels[channel]:
                        channels[channel]['upcoming'] = upcoming
                    elif upcoming.get('start')[0:17] == channels[channel]['upcoming'].get('start')[0:17] and upcoming.get('id') != channels[channel]['upcoming'].get('id'):
                        channelresults[channel] = self.getStreamInfos(upcoming, inputstreamAdaptive)
                    self.buildStreamItem(upcoming, channel, channelresults[channel], inputstreamAdaptive)

        # Render upcoming streams last for better list item order.
        if showFullSchedule:
            addDirectory('[COLOR red]----------------[/COLOR]', None, self.defaultbackdrop, "", "", 'getLive', self.pluginhandle)
            for channel in channels:
                for upcoming in channelresults[channel]['items']:
                    if not 'upcoming' in channels[channel] or channels[channel]['upcoming'].get('id') != upcoming.get('id'):
                        self.buildStreamItem(upcoming, channel, channelresults[channel], inputstreamAdaptive, False)

    # Restart callback.
    def liveStreamRestart(self, link, protocol):
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
            restart_urls = None
            restart_url = None
            try:
                restart_urls = result['_embedded']['channel']['restart_urls']
            except AttributeError:
                pass
            else:
                for x in ('android', 'default'):
                    if x in restart_urls:
                        restart_url = restart_urls[x]
                        if restart_url:
                            break
            if not restart_url:
                raise Exception("restart url not found in livestream/%s result" % (link, ))
            m = re.search(r"/livestreams/([^/]+)/sections/[^\?]*\?(?:.+&|)?X-Api-Key=([^&]+)", restart_url)
            if m:
                bitmovinStreamId, ApiKey = m.groups()
            else:
                raise Exception("unable to parse restart url: %s" % ( restart_url, ))
            response = url_get_request(restart_url)  # nosec
            response_raw = response.read().decode('UTF-8')
            section = json.loads(response_raw)[0]
            section_id = section.get('id')
            timestamp = section.get('metaData').get('timestamp')
            streamingURL = 'https://playerapi-restarttv.ors.at/livestreams/%s/sections/%s/manifests/%s/?startTime=%s&X-Api-Key=%s' % (bitmovinStreamId, section_id, protocol, timestamp, ApiKey)
            listItem = createListItem(title, image, description, duration, time.strftime('%Y-%m-%d', date), result.get('SSA').get('channel').upper(), streamingURL, True, False, self.defaultbackdrop, self.pluginhandle)
            return streamingURL, listItem

    def __makeRequest(self, url):
        return url_get_request(self.__urlBase + url, self.httpauth)

    def __makeRequestV4(self, url):
        return url_get_request(self.__urlBaseV4 + url, self.httpauth)

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
