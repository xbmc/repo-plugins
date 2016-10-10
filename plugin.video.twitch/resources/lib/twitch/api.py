# -*- encoding: utf-8 -*-
from urllib import quote_plus
from constants import Keys, Urls
from utils import JSONScraper, M3UPlaylist
from exception import TwitchException


class TwitchTV(object):
    '''
    Uses Twitch API to fetch json-encoded objects
    every method returns a dict containing the objects\' values
    '''

    def __init__(self, logger):
        self.logger = logger
        self.scraper = JSONScraper(logger)

    def getFeaturedStream(self):
        url = ''.join([Urls.STREAMS, Keys.FEATURED])
        return self._fetchItems(url, Keys.FEATURED)

    def getGames(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.GAMES, Keys.TOP, options])
        return self._fetchItems(url, Keys.TOP)

    def getChannels(self, offset=0, limit=10):
        options = Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
        url = ''.join([Urls.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getGameStreams(self, gameName, offset=0, limit=10):
        quotedName = quote_plus(gameName)
        options = Urls.OPTIONS_OFFSET_LIMIT_GAME.format(offset, limit, quotedName)
        url = ''.join([Urls.BASE, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def searchStreams(self, query, offset=0, limit=10):
        quotedQuery = quote_plus(query)
        options = Urls.OPTIONS_OFFSET_LIMIT_QUERY.format(offset, limit, quotedQuery)
        url = ''.join([Urls.SEARCH, Keys.STREAMS, options])
        return self._fetchItems(url, Keys.STREAMS)

    def getFollowingStreams(self, username):
        # Get ChannelNames
        followingChannels = self.getFollowingChannelNames(username)
        channelNames = self._filterChannelNames(followingChannels)

        # get Streams of that Channels
        options = Urls.OPTIONS_OFFSET_LIMIT
        options += '&channel=' + ','.join([channels[Keys.NAME] for channels in channelNames])
        rawurl = ''.join([Urls.BASE, Keys.STREAMS, options])

        live = []
        limit = 100
        offset = 0
        while True:
            url = rawurl.format(offset, limit)
            temp = self._fetchItems(url, Keys.STREAMS)
            if len(temp) == 0:
                break
            live += temp
            offset += limit

        channels = {Keys.LIVE: live, Keys.OTHERS: channelNames}
        return channels

    def getFollowingGames(self, username):
        acc = []
        limit = 100
        offset = 0
        quotedUsername = quote_plus(username)
        baseurl = Urls.FOLLOWED_GAMES.format(quotedUsername)
        while True:
            url = baseurl + Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
            temp = self._fetchItems(url, Keys.FOLLOWS)
            if len(temp) == 0:
                break
            acc += temp
            offset += limit
        return acc

    def getFollowerVideos(self, username, offset, broadcast_type):
        url = Urls.CHANNEL_VIDEOS.format(username, offset, broadcast_type)
        items = self.scraper.getJson(url)
        return {Keys.TOTAL: items[Keys.TOTAL], Keys.VIDEOS: items[Keys.VIDEOS]}

    def getVideoTitle(self, _id):
        url = Urls.VIDEO_INFO.format(_id)
        return self._fetchItems(url, Keys.TITLE)

    def getVideo(self, _id):
        url = Urls.VIDEO_INFO.format(_id)
        return self.scraper.getJson(url)

    def getStreamInfo(self, channelname):
        # Get Stream info
        url = ''.join([Urls.STREAMS, channelname])
        stream = self._fetchItems(url, Keys.STREAM)
        if stream:
            return stream
        else:
            raise TwitchException(TwitchException.STREAM_OFFLINE)

    def __getChunkedVideo(self, _id, oauthtoken):
        # twitch site queries chunked playlists also with token
        # not necessary yet but might change (similar to vod playlists)
        url = Urls.VIDEO_PLAYLIST.format(_id) + '?oauth_token=' + oauthtoken
        return self.scraper.getJson(url)

    def __getVideoPlaylistChunkedArchived(self, _id, maxQuality, oauthtoken):
        vidChunks = self.__getChunkedVideo(_id, oauthtoken)
        if vidChunks[Keys.CHUNKS].get(Keys.QUALITY_LIST_VIDEO[maxQuality]):
            # preferred quality is not None -> available
            chunks = vidChunks[Keys.CHUNKS][Keys.QUALITY_LIST_VIDEO[maxQuality]]
        else:
            # preferred quality is not available TODO best match
            chunks = vidChunks[Keys.CHUNKS][Keys.QUALITY_LIST_VIDEO[0]]

        title = self.getVideoTitle(_id)
        itemTitle = '%s - Part {0} of %s' % (title, len(chunks))

        playlist = [('', ('', vidChunks[Keys.PREVIEW]))]
        curN = 0
        for chunk in chunks:
            curN += 1
            playlist += [(chunk[Keys.URL], (itemTitle.format(curN), vidChunks[Keys.PREVIEW]))]

        return playlist

    def __getVideoPlaylistVod(self, _id, maxQuality, oauthtoken):
        playlist = [('', ())]
        vodid = _id[1:]
        url = Urls.VOD_TOKEN.format(vodid) + '?oauth_token=' + oauthtoken
        access_token = self.scraper.getJson(url)

        playlistQualitiesUrl = Urls.VOD_PLAYLIST.format(
            vodid,
            access_token[Keys.TOKEN],
            access_token[Keys.SIG])
        playlistQualitiesData = self.scraper.downloadWebData(playlistQualitiesUrl)

        qualityList = Keys.QUALITY_LIST_STREAM
        if 'NAME="360p30"' not in playlistQualitiesData and 'NAME="360p"' not in playlistQualitiesData:
            qualityList = Keys.OLD_QUALITY_LIST_STREAM
        playlistQualities = M3UPlaylist(playlistQualitiesData, qualityList)

        vodUrl = playlistQualities.getQuality(maxQuality)
        playlist += [(vodUrl, ())]

        return playlist

    def getVideoPlaylist(self, _id, maxQuality, oauthtoken):
        playlist = [(), ()]
        if _id.startswith(('a', 'c')):
            playlist = self.__getVideoPlaylistChunkedArchived(_id, maxQuality, oauthtoken)
        elif _id.startswith('v'):
            playlist = self.__getVideoPlaylistVod(_id, maxQuality, oauthtoken)
        return playlist

    def getFollowingChannelNames(self, username):
        acc = []
        limit = 100
        offset = 0
        quotedUsername = quote_plus(username)
        baseurl = Urls.FOLLOWED_CHANNELS.format(quotedUsername)
        while True:
            url = baseurl + Urls.OPTIONS_OFFSET_LIMIT.format(offset, limit)
            temp = self._fetchItems(url, Keys.FOLLOWS)
            if len(temp) == 0:
                break
            acc += temp
            offset += limit
        return acc

    def getTeams(self, index):
        return self._fetchItems(Urls.TEAMS.format(str(index * 25)), Keys.TEAMS)

    def getTeamStreams(self, teamName):
        '''
        :param teamName: string: team name
        Consider this method to be unstable, because the
        requested resource is not part of the official Twitch API
        '''
        quotedTeamName = quote_plus(teamName)
        url = Urls.TEAMSTREAM.format(quotedTeamName)
        return self._fetchItems(url, Keys.CHANNELS)

    # gets playable livestream url
    def getLiveStream(self, channelName, maxQuality):
        # Get Access Token (not necessary at the moment but could come into effect at any time)
        tokenurl = Urls.CHANNEL_TOKEN.format(channelName)
        channeldata = self.scraper.getJson(tokenurl)
        channeltoken = channeldata[Keys.TOKEN]
        channelsig = channeldata[Keys.SIG]

        # Download and Parse Multiple Quality Stream Playlist
        try:
            hls_url = Urls.HLS_PLAYLIST.format(channelName, channelsig, channeltoken)
            data = self.scraper.downloadWebData(hls_url)
            qualityList = Keys.QUALITY_LIST_STREAM
            if 'NAME="360p30"' not in data:
                qualityList = Keys.OLD_QUALITY_LIST_STREAM
            playlist = M3UPlaylist(data, qualityList)
            return playlist.getQuality(maxQuality)

        except TwitchException:
            # HTTP Error in download web data -> stream is offline
            raise TwitchException(TwitchException.STREAM_OFFLINE)

    @staticmethod
    def _filterChannelNames(channels):
        tmp = [{Keys.DISPLAY_NAME: item[Keys.CHANNEL][Keys.DISPLAY_NAME],
                Keys.NAME: item[Keys.CHANNEL][Keys.NAME],
                Keys.LOGO: item[Keys.CHANNEL][Keys.LOGO],
                Keys.PROFILE_BANNER: item[Keys.CHANNEL][Keys.PROFILE_BANNER],
                Keys.VIDEO_BANNER: item[Keys.CHANNEL][Keys.VIDEO_BANNER]}
               for item in channels]
        return sorted(tmp, key=lambda k: k[Keys.DISPLAY_NAME])

    def _fetchItems(self, url, key):
        items = self.scraper.getJson(url)
        return items[key] if items else []
