from de.generia.kodi.plugin.backend.zdf.Teaser import Teaser
from de.generia.kodi.plugin.backend.zdf.RubricResource import RubricResource

    
class VideoResource(RubricResource):

    def __init__(self, url):
        super(VideoResource, self).__init__(url)
            
    def parse(self):
        super(VideoResource, self).parse()


    def _isModule(self, class_):
        return class_.find('b-video-module') != -1
    
    def _parseModule(self, pos, contentPattern, textPattern, datePattern, moduleType):
        match = None
        
        teaser = Teaser()
        pos = teaser.parseApiToken(self.content, pos)
        self.apiToken = teaser.apiToken
        
        return match
