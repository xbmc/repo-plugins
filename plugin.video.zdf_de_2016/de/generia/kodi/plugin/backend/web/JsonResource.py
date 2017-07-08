import json

from de.generia.kodi.plugin.backend.web.Resource import Resource

def getValue(obj, key):
    if key in obj:
        return obj[key]
    return None

class JsonResource(Resource):

        
    def __init__(self, url, accept='application/json'):
        super(JsonResource, self).__init__(url, accept)
        
    def parse(self):
        super(JsonResource, self).parse()
        self.content = json.loads(self.content)
