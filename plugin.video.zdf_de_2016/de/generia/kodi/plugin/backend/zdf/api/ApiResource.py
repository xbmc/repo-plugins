from de.generia.kodi.plugin.backend.web.JsonResource import JsonResource


class ApiResource(JsonResource):
    
    def __init__(self, url, apiToken, accept='application/json'):
        super(ApiResource, self).__init__(url, accept)
        self.apiToken = apiToken
        
                
    def _createRequest(self):
        request = super(ApiResource, self)._createRequest()
        request.add_header('Api-Auth', 'Bearer ' + self.apiToken)
        return request
        
