from de.generia.kodi.plugin.backend.web.Resource import Resource
from de.generia.kodi.plugin.backend.zdf.Regex import compile

bandwidthPattern = compile('BANDWIDTH=([^,]*),')

class PlaylistResource(Resource):

    def __init__(self, url, accept='application/vnd.apple.mpegurl'):
        super(PlaylistResource, self).__init__(url, accept)
        self.playlist = None
    
    def getPlaylist(self):
        return self.playlist
            
    def parse(self):
        super(PlaylistResource, self).parse()
        lines = self.content.split("\n")
        
        programMap = self._parseProgramMap(lines)
        maxBandwith = self._getMaxBandwidth(programMap)
        if maxBandwith is None:
            return
        filteredLines = self._filterPlaylist(lines, maxBandwith, programMap)
        self.playlist = "\n".join(filteredLines)
        
    def _parseProgramMap(self, lines):
        bandwith = None
        programMap = dict()
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                if line.startswith("#EXT-X-STREAM-INF:"):
                    match = bandwidthPattern.search(line)
                    if match is not None:
                        bandwith = int(match.group(1))
            elif line != "":
                streamUrl = line
                if bandwith is not None:
                    programMap[bandwith] = streamUrl
        return programMap

    def _getMaxBandwidth(self, programMap):
        maxBandwidth = -1
        for bandwidth in programMap.keys():
            if bandwidth > maxBandwidth:
                maxBandwidth = bandwidth
        if maxBandwidth != -1:
            return maxBandwidth
        return None
    
    def _filterPlaylist(self, lines, maxBandwidth, programMap):
        filteredLines = []
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                if line.startswith("#EXT-X-STREAM-INF:"):
                    match = bandwidthPattern.search(line)
                    if match is not None:
                        bandwith = int(match.group(1))
                        if bandwith == maxBandwidth:
                            streamUrl = programMap[bandwith]
                            streamUrl = self._getAbsoluteUrl(self.url, streamUrl)
                            filteredLines.append(line)
                            filteredLines.append(streamUrl)
                else:
                    filteredLines.append(line)
        return filteredLines
        
