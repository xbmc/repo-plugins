import urllib2
import json
from StringIO import StringIO

class onAir:
    def getNowNext(self):
        url = "http://www.rai.it/dl/portale/html/palinsesti/static/palinsestoOraInOnda.html?output=json" 
        response = json.load(urllib2.urlopen(url))
        return response

    def getNowNextWR(self, stationId):
        # stationId = {fd4, fd5}
        # disabled for {wr6, wr7, wr8}
        url = "http://service.rai.it/xml2json.php?jsonp=?&xmlurl=http://frog.prodradio.rai.it/orainonda/%s/onair_%s.xml" % (stationId, stationId)
        text = urllib2.urlopen(url).read()
        text = text[2:-2]
        io = StringIO(text)
        response = json.load(io)
        return response["xml"]["radio"]

##onair = onAir()
###epg = onair.getNowNext()
###print epg["curr"]["radio 1"]["titolo"]
###print epg["curr"]["radio 1"]["ora"]
###print epg["next"]["radio 1"]["titolo"]
###print epg["next"]["radio 1"]["ora"]
##
###for station in epg["curr"].keys():
###    print station
##print onair.getNowNextWR("fd5")["now_playing"]["music"]["title"]
##print onair.getNowNextWR("fd5")["next_event"][0]["music"]["title"]

