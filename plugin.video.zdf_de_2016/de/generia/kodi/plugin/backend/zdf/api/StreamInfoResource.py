from de.generia.kodi.plugin.backend.zdf.api.ApiResource import ApiResource


class StreamInfoResource(ApiResource):

    def __init__(self, url, apiToken):
        super(StreamInfoResource, self).__init__(url, apiToken)
                    
    def parse(self):
        super(StreamInfoResource, self).parse()
        priorityList = self.content['priorityList']
        priority = priorityList[0]
        formitaeten = priority['formitaeten']
        formitaet = formitaeten[0]
        self.mimeType = formitaet['mimeType']
        qualities = formitaet['qualities']
        quality = qualities[0]
        self.hd = quality['hd']
        self.quality = quality['quality']
        audio = quality['audio']
        tracks = audio['tracks']
        track = tracks[0]
        
        self.streamUrl = track['uri']

