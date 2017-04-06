from de.generia.kodi.plugin.backend.web.Resource import Resource

class HtmlResource(Resource):

    def __init__(self, url, accept='text/html'):
        super(HtmlResource, self).__init__(url, accept)
        
    def parse(self):
        super(HtmlResource, self).parse()
