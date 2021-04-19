# -*- coding: utf-8 -*-
import sys
import json
import unicodedata
import resources.lib.utils as utils

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2

else:
    import urllib2

class RaiPlayRadio:
    # Raiplay android app
    UserAgent = "okhttp/3.9.1"
    MediapolisUserAgent = "Radio/3.0.2 (Linux;Android 4.2.2) ExoPlayerLib/2.5.4"
    
    noThumbUrl = "http://www.raiplayradio.it/dl/components/img/radio/player/placeholder_img.png"
    
    # http://www.rai.it/dl/rairadio/mobile/config/RaiRadioConfig.json
    baseUrl = "http://www.raiplayradio.it/"
    channelsUrl = "http://www.raiplayradio.it/dirette/ContentSet-8e2a3414-bbfd-4a72-852b-7d827dc00e7e.html?json"
    localizeUrl = "http://mediapolisgs.rai.it/relinker/relinkerServlet.htm?cont=201342"
    palinsestoUrl = "http://www.raiplayradio.it/dl/palinsesti/Page-a47ba852-d24f-44c2-8abb-0c9f90187a3e-json.html?canale=[nomeCanale]&giorno=[dd-mm-yyyy]&mode=light"
    AzTvShowPath = "/dl/RaiTV/RaiRadioMobile/Prod/Config/programmiAZ-elenco.json"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.UserAgent)]
        urllib2.install_opener(opener)
    
    def getCountry(self):
        try:
            response = utils.checkStr(urllib2.urlopen(self.localizeUrl).read())
        except:
            response = "ERROR"
        return response
        
    def getChannels(self):
        response = json.loads(utils.checkStr(urllib2.urlopen(self.channelsUrl).read()))
        return response["dirette"]
        
    def getProgrammes(self, channelName, epgDate):
        channelTag = channelName.replace(" ", "")
        channelTag = unicodedata.normalize('NFD', channelTag).encode('ascii', 'ignore')
        url = self.palinsestoUrl
        url = url.replace("[nomeCanale]", channelTag)
        url = url.replace("[dd-mm-yyyy]", epgDate)
        response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
        return response[channelName][0]["palinsesto"][0]["programmi"]
    
    def getAudioMetadata(self, pathId):
        url = self.getUrl(pathId)
        response = json.loads(utils.checkStr(urllib2.urlopen(url).read()))
        return response["audio"]
    
    def getUrl(self, pathId):
        pathId = pathId.replace(" ", "%20")
        if pathId[0:2] == "//":
            url = "http:" + pathId
        elif pathId[0] == "/":
            url = self.baseUrl[:-1] + pathId
        else:
            url = pathId
        return url
        
    def getThumbnailUrl(self, pathId):
        if pathId == "":
            url = self.noThumbUrl
        else:
            url = self.getUrl(pathId)
            url = url.replace("[RESOLUTION]", "256x-")
        return url
 
