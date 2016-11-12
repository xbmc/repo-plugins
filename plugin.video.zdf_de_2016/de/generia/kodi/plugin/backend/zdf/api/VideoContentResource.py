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
        
        if 'http://zdf.de/rels/category' in self.content:
            category = self.content['http://zdf.de/rels/category']
            self.genre = category.get('title')
            
        if 'teaserImageRef' in self.content:
            teaserImageRef = self.content['teaserImageRef']
            layouts = teaserImageRef['layouts']
            if 'original' in layouts:
                self.image = layouts['original']
            else:
                for value in layouts.values():
                    self.image = value
                    break
            
        self.url = None
        if 'mainVideoContent' in self.content:
            mainVideoContent = self.content['mainVideoContent']
            target = mainVideoContent['http://zdf.de/rels/target']
            self.streamInfoUrl = self.apiBaseUrl + target['http://zdf.de/rels/streams/ptmd']
