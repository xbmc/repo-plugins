from de.generia.kodi.plugin.backend.zdf.api.ApiResource import ApiResource


class StreamInfoResource(ApiResource):

    def __init__(self, url, apiToken):
        super(StreamInfoResource, self).__init__(url, apiToken)
                    
    def parse(self):
        super(StreamInfoResource, self).parse()
        priorityList = self.content.get('priorityList')
        priority = priorityList[0]
        formitaeten = priority.get('formitaeten')
        formitaet = formitaeten[0]
        self.mimeType = formitaet.get('mimeType')
        qualities = formitaet.get('qualities')
        quality = qualities[0]
        self.hd = quality.get('hd')
        self.quality = quality.get('quality')
        audio = quality.get('audio')
        tracks = audio.get('tracks')
        track = tracks[0]
        
        self.streamUrl = track.get('uri')

