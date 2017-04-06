from de.generia.kodi.plugin.backend.web.JsonResource import JsonResource


class ConfigurationResource(JsonResource):

    def __init__(self, url):
        super(ConfigurationResource, self).__init__(url)
            
    def parse(self):
        super(ConfigurationResource, self).parse()

        self.apiToken = self.content['apiToken']
        
        