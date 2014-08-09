import urllib2
import json

class Replay:
    # Channels at
    # http://www.rai.tv/dl/RaiTV/iphone/android/smartphone/advertising_config.html
  
    def getProgrammes(self, channelId, channelTag, epgDate):
        url = "http://www.rai.tv/dl/portale/html/palinsesti/replaytv/static/%s_%s.html" % (channelTag, epgDate)
        print "Replay TV URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        return response[str(channelId)][epgDate.replace('_', '-')]

