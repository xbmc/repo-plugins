import urllib2,json
import utils

class Request:
    @staticmethod
    def getJson(url, headers={}):
        utils.log("Requesting %s..." % url)

        request = urllib2.Request(url, None, headers);
        response = str(urllib2.urlopen(request).read())
        #Read JSONP too
        return json.loads(response[response.find("{"):])

    @staticmethod
    def get(url, headers={}):
        utils.log("Requesting %s..." % url)
        
        request = urllib2.Request(url, None, headers);
        response = str(urllib2.urlopen(request).read())
        return response