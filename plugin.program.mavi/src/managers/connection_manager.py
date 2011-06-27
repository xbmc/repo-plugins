import urllib

class ConnectionManager:
    
    def doRequest(self, url):
        req = urllib.urlopen(url)
        data = req.read()
        req.close()
        return data