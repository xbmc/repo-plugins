import json
try:
    import xbmc
except:
    print "Outsided xbmc"
    
from exception import QobuzXbmcError
import pprint
from debug import log

def showNotification(**ka):
    rpc = XbmcRPC()
    return rpc.showNotification(**ka)

def ping(**ka):
    rpc = XbmcRPC()
    return rpc.ping(**ka).result()

def getInfoLabels(**ka):
    rpc = XbmcRPC()
    return rpc.getInfoLabels(**ka).result()

"""
    @class: JsonRequest
"""
class JsonRequest:
    def __init__(self, method):
        self.method = method
        self.version = '2.0'
        self.parameters = {}
        self.id = None

    def add_parameters(self, kDict):
        for label in kDict:
            self.parameters[label] = kDict[label]

    def to_json(self):
        jDict = {
                'method': self.method,
                'jsonrpc': self.version,
                'params': self.parameters,
        }
        if self.id:
            jDict['id'] = self.id
        data = json.dumps(jDict)
        print "Data: %s" % (data)
        return data
    
class JsonResponse:
    
    def __init__(self, raw_data):
        self.raw_data = None
        self.id = None
        if raw_data:
            self.set_raw_data(raw_data)

    def error(self):
        if not self.raw_data:
            return ''
        if 'error' in self.raw_data:
            return pprint.pformat(self.raw_data['error'])
        return ''
        
    def result(self):
        error = self.error()
        if error:
            log(self, "Error: %s" % (error))
        if not self.raw_data:
            return {}
        if not 'result' in self.raw_data:
            return {}
        return self.raw_data['result']
    
    def set_raw_data(self, data):
        if not data: return False
        self.raw_data = json.loads(data)
        return True
        
"""
    @class: XbmcRPC
"""
class XbmcRPC:
    def __init__(self):
        pass

    def send(self, request):
        if not request:
            raise QobuzXbmcError(
                who=self, what='missing_parameter', additional='request')
        return JsonResponse(xbmc.executeJSONRPC(request.to_json()))

    def ping(self):
        request = JsonRequest('JSONRPC.Ping')
        request.id = 1
        return self.send(request)

    def showNotification(self, **ka):
        request = JsonRequest('GUI.ShowNotification')
        request.add_parameters({
            'title' : ka['title'],
            'message': ka['message']
        })
        if ka['displaytime']:
            request.add_parameters({'displaytime': ka['displaytime']})
        if ka['image']:
            request.add_parameters({'image': ka['image']})
        return self.send(request)
    
    def getInfoLabels(self, labels):
        request = JsonRequest('XBMC.GetInfoLabels')
        request.id = 1
        request.add_parameters({'labels': labels})
        return self.send(request)

    def getSongDetails(self, sid):
        request = JsonRequest('AudioLibrary.GetSongDetails')
        request.id = 1
        request.add_parameters({'songid': int(sid), 
                                "properties": [      "title", 
      "artist", 
      "albumartist", 
      "genre", 
      "year", 
      "rating", 
      "album", 
      "track", 
      "duration", 
      "comment", 
      "lyrics", 
      "musicbrainztrackid", 
      "musicbrainzartistid", 
      "musicbrainzalbumid", 
      "musicbrainzalbumartistid", 
      "playcount", 
      "fanart", 
      "thumbnail", 
      "file", 
      "albumid", 
      "lastplayed", 
      "disc", 
      "genreid", 
      "artistid", 
      "displayartist", 
      "albumartistid"]})
        return self.send(request)

rpc = XbmcRPC()