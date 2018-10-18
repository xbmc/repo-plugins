from de.generia.kodi.plugin.backend.zdf.api.ApiResource import ApiResource


class VideoContentResource(ApiResource):
    
    def __init__(self, url, apiBaseUrl, apiToken):
        super(VideoContentResource, self).__init__(url, apiToken, 'application/vnd.de.zdf.v1.0+json')
        self.apiBaseUrl = apiBaseUrl

    def parse(self):
        super(VideoContentResource, self).parse()
        
        self.title = self.content.get('title') 
        self.text = self.content.get('teasertext')
        self.tvService = self.content.get('tvService')
        self.date = self.content.get('editorialDate')
        
        self.genre = None
        if 'http://zdf.de/rels/category' in self.content:
            category = self.content['http://zdf.de/rels/category']
            self.genre = category.get('title')

        self.image = None            
        if 'teaserImageRef' in self.content:
            teaserImageRef = self.content.get('teaserImageRef')
            layouts = teaserImageRef.get('layouts')
            if 'original' in layouts:
                self.image = layouts.get('original')
            else:
                for value in layouts.values():
                    self.image = value
                    break
            
        self.duration = None
        self.streamInfoUrl = None
        if 'mainVideoContent' in self.content:
            mainVideoContent = self.content.get('mainVideoContent')
            target = mainVideoContent.get('http://zdf.de/rels/target')
            playerId = 'ngplayer_2_3'
            streamInfoUrl = target.get('http://zdf.de/rels/streams/ptmd-template')
            if streamInfoUrl is not None:
                streamInfoUrl = streamInfoUrl.replace('{playerId}', playerId)
            else:
                streamInfoUrl = target.get('http://zdf.de/rels/streams/ptmd-template')
            if streamInfoUrl is not None:
                self.streamInfoUrl = self.apiBaseUrl + streamInfoUrl
            duration = target.get('duration')
            if duration is not None:
                self.duration = int(duration)
