import urllib

import xbmc
import xbmcgui
import xbmcplugin

from urllib2 import HTTPError 

from de.generia.kodi.plugin.backend.zdf.VideoResource import VideoResource

from de.generia.kodi.plugin.backend.zdf.api.VideoContentResource import VideoContentResource
from de.generia.kodi.plugin.backend.zdf.api.StreamInfoResource import StreamInfoResource
from de.generia.kodi.plugin.backend.zdf.PlaylistResource import PlaylistResource        

from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class PlayVideo(Pagelet):
    
    def __init__(self, playerStore, filterMasterPlaylist, disableSubtitles):
        super(Pagelet, self).__init__()
        self.playerStore = playerStore
        self.filterMasterPlaylist = filterMasterPlaylist
        self.disableSubtitles = disableSubtitles

    def service(self, request, response):
        contentName = request.getParam('contentName')
        title = request.getParam('title')
        videoUrl = request.getParam('videoUrl')
        date = request.getParam('date')
        genre = request.getParam('genre')

        # get api-token handling parameters
        self.videoUrl = request.getParam('videoUrl')
        self.apiToken = request.getParam('apiToken')
        if self.apiToken is None:
            self.apiToken = self.playerStore.getApiToken()
            if self.apiToken is None:
                self._refreshApiToken()
            
        item = None
        if contentName is not None:
            try:
                dialog = xbmcgui.DialogProgressBG()
                dialog.create(self._(32007), self._(32008))
                videoContentUrl = Constants.apiContentUrl + contentName + '.json?profile=player2'
                self.debug("downloading video-content-url '{1}' ...", videoContentUrl)
                videoContent = self._getVideoContent(videoContentUrl)
                
                if videoContent.streamInfoUrl is None:
                    self.warn("can't find stream-info-url in video-content '{1}' in content '{2}'", contentName, videoContent.content)
                    response.sendError(self._(32011) + " '" + contentName +"'", Action('SearchPage'))
                    return
            
                dialog.update(percent=50, message=self._(32009))
                self.debug("downloading stream-info-url '{1}' ...", videoContent.streamInfoUrl)
                streamInfo = self._getStreamInfo(videoContent.streamInfoUrl)
                
                rawPlaylistUrl = streamInfo.streamUrl
                if rawPlaylistUrl is None:
                    self.warn("can't find stream-url in stream-info-url '{1}' in content '{2}'", videoContent.streamInfoUrl, streamInfo.content)
                    response.sendError(self._(32012) + " '" + contentName +"'", Action('SearchPage'))
                    return

                # finding best stream url
                dialog.update(percent=70, message=self._(32044))
                self.debug("downloading master playlist '{1}' ...", rawPlaylistUrl)
                url = self._getPlaylistUrl(rawPlaylistUrl)
                
                title = videoContent.title
                text = videoContent.text
                infoLabels = {}
                infoLabels['title'] = title
                infoLabels['sorttitle'] = title
                infoLabels['genre'] = genre
                #infoLabels['plot'] = text
                #infoLabels['plotoutline'] = text
                infoLabels['tvshowtitle'] = title
                infoLabels['tagline'] = text
                if videoContent.duration is not None:
                    infoLabels['duration'] = videoContent.duration
                infoLabels['mediatype'] = 'video'

                if date is not None and date != "":
                    infoLabels['date'] = date
        
                item = xbmcgui.ListItem(title, text)
                item.setPath(url)
                item.setInfo(type="Video", infoLabels=infoLabels)
                image = videoContent.image
                if image is not None:
                    item.setArt({'poster': image, 'banner': image, 'thumb': image, 'icon': image, 'fanart': image})

                # set subtitles
                if not self.disableSubtitles:
                    self._setSubTitles(item, streamInfo.subTitlesUrl)
                
                dialog.update(percent=90, message=self._(32010))
                self.info("setting resolved url='{1}' ...", url)
                xbmcplugin.setResolvedUrl(response.handle, True, item)
            finally:
                dialog.close();
            
    def _getStreamInfo(self, streamInfoUrl):
            streamInfo = None
            try:
                streamInfo = StreamInfoResource(streamInfoUrl, self.apiToken)
                self._parse(streamInfo)
            except HTTPError as e:
                # check for forbidden, caused by wrong api-token
                if e.code != 403:
                    raise e
                
                # try again with more specific video api-token
                if not self._refreshApiToken():
                    raise e

                streamInfo = StreamInfoResource(streamInfoUrl, self.apiToken)
                self._parse(streamInfo)
            
            return streamInfo
            
    def _getVideoContent(self, videoContentUrl):
            videoContent = None
            try:
                videoContent = VideoContentResource(videoContentUrl, Constants.apiBaseUrl, self.apiToken)
                self._parse(videoContent)
            except HTTPError as e:
                # check for forbidden, caused by wrong api-token
                if e.code != 403:
                    raise e
                
                # try again with more specific video api-token
                if not self._refreshApiToken():
                    raise e
                
                videoContent = VideoContentResource(videoContentUrl, Constants.apiBaseUrl, self.apiToken)
                self._parse(videoContent)
            
            return videoContent

    def _refreshApiToken(self):
        if self.videoUrl is None:
            self.error("can't refresh api-token: videoUrl is not set")
            return False
        
        video = VideoResource(Constants.baseUrl + self.videoUrl)
        self._parse(video)
        apiToken = video.apiToken
        self.playerStore.setApiToken(apiToken)
        self.apiToken = apiToken
        return True
    
    def _setSubTitles(self, item, subTitlesUrl):            
        if subTitlesUrl is not None:
            try:
                item.addStreamInfo('subtitle', {'language': 'de'})
                item.setSubtitles([subTitlesUrl])
                self.info("setting sub-titles-url='{1}' ...", subTitlesUrl)
            except AttributeError:
                self.info("no sub-titles supported before Kodi 14.x 'Helix', skipping subtitles ...")
        else:
            self.info("no sub-titles-url available in stream-info, skipping subtitles ...")
 
    def _getPlaylistUrl(self, rawPlaylistUrl):
        if not self.filterMasterPlaylist:
            return rawPlaylistUrl
        
        masterResource = PlaylistResource(rawPlaylistUrl)
        try:
            self._parse(masterResource)
        except HTTPError as e:
            self.warn("could not load master playlist '{1}', falling back to raw playlist...", rawPlaylistUrl)
            return rawPlaylistUrl

        playlist = masterResource.getPlaylist()
        if playlist is not None:
            self.playerStore.storePlaylist(playlist)
            return self.playerStore.getPlaylistUrl()
        self.warn("could not filter playlist '{1}', falling back to raw playlist...", rawPlaylistUrl)
        return rawPlaylistUrl
    