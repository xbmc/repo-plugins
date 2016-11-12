import urllib

import xbmc
import xbmcgui

from de.generia.kodi.plugin.backend.zdf.api.VideoContentResource import VideoContentResource
from de.generia.kodi.plugin.backend.zdf.api.StreamInfoResource import StreamInfoResource

from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class PlayVideo(Pagelet):
 
    def service(self, request, response):
        apiToken = request.getParam('apiToken')
        contentName = request.getParam('contentName')

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

                image = videoContent.image
                item = xbmcgui.ListItem(videoContent.title)
                item.setArt({'poster': image, 'banner': image, 'thumb': image, 'icon': image, 'fanart': image})
                
                dialog.update(percent=90, message=self._(32010))
                self.info("Timer - starting player with url='{1}' ...", url)
                start = self.log.start()
                xbmc.Player().play(url, item)
                self.info("Timer - starting player with url='{1}' ... done. [{2} ms]", url, self.log.stop(start))
    
            finally:
                dialog.close();
            
