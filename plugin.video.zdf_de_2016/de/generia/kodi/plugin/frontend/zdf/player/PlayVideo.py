import urllib

import xbmc
import xbmcgui
import xbmcplugin

from de.generia.kodi.plugin.backend.zdf.api.VideoContentResource import VideoContentResource
from de.generia.kodi.plugin.backend.zdf.api.StreamInfoResource import StreamInfoResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class PlayVideo(Pagelet):
 
    def service(self, request, response):
        apiToken = request.getParam('apiToken')
        contentName = request.getParam('contentName')
        title = request.getParam('title')
        date = request.getParam('date')
        genre = request.getParam('genre')

        item = None
        if contentName is not None:
            try:
                dialog = xbmcgui.DialogProgressBG()
                dialog.create(self._(32007), self._(32008))
                videoContentUrl = Constants.apiBaseUrl + '/content/documents/' + contentName + '.json?profile=player'
                self.debug("downloading video-content-url '{1}' ...", videoContentUrl)
                videoContent = VideoContentResource(videoContentUrl, Constants.apiBaseUrl, apiToken)
                self._parse(videoContent)
                
                if videoContent.streamInfoUrl is None:
                    self.warn("can't find stream-info-url in video-content '{1}' in content '{2}'", contentName, videoContent.content)
                    response.sendError(self._(32011) + " '" + contentName +"'", Action('SearchPage'))
                    return
            
                dialog.update(percent=50, message=self._(32009))
                self.debug("downloading stream-info-url '{1}' ...", videoContent.streamInfoUrl)
                streamInfo = StreamInfoResource(videoContent.streamInfoUrl, apiToken)
                self._parse(streamInfo)
                
                url = streamInfo.streamUrl
                if url is None:
                    self.warn("PlayVideo - can't find stream-url in stream-info-url '{1}' in content '{2}'", videoContent.streamInfoUrl, streamInfo.content)
                    response.sendError(self._(32012) + " '" + contentName +"'", Action('SearchPage'))
                    return

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
                
                dialog.update(percent=90, message=self._(32010))
                self.info("setting resolved url='{1}' ...", url)
                xbmcplugin.setResolvedUrl(response.handle, True, item)
            finally:
                dialog.close();
            
