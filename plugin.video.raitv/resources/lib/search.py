# -*- coding: utf-8 -*-
import sys
import json
import urllib
import resources.lib.utils as utils
import xbmc

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2
    import html.parser as HTMLParser
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    
else:
    import urllib2
    import HTMLParser
    import urlparse
    from urllib import urlencode

import resources.lib.utils as utils

class Search:
    baseUrl = "http://www.rai.it"

    suggestionUrl = "https://www.raiplay.it/atomatic/raiplay-search-service/api/v2/suggestion"
    # effettuare POST con parametro {'text': stringa da cercare}
    searchUrl = "https://www.raiplay.it/atomatic/raiplay-search-service/api/v3/search"
    # effettuare POST con parametri {   "param": stringa da cercare,   "page": 0, "pageSize": 12 }

    newsArchives = {
        "TG1": "NomeProgramma:TG1^Tematica:Edizioni integrali",
        "TG2": "NomeProgramma:TG2^Tematica:Edizione integrale",
        "TG3": "NomeProgramma:TG3^Tematica:Edizioni del TG3"
            }
    
    newsProviders = {
        "TG1": "Tematica:TG1",
        "TG2": "Tematica:TG2",
        "TG3": "Tematica:TG3",
        "Rai News": "Tematica:Rai News",
        "Rai Parlamento": "PageOB:Page-f3f817b3-1d55-4e99-8c36-464cea859189"
            }
    def searchByName(self, string):
        xbmc.log("Raiplay: Searching with key: " + string, xbmc.LOGINFO)
        s = []
        
        # Build the request and send to server
        req = urllib2.Request(self.searchUrl, method="POST")
        req.add_header('Content-Type', 'application/json')
        post_data = { "param": string, "page": 0, "pageSize": 12 }
        post_data = json.dumps(post_data)
        post_data = post_data.encode()
        r = urllib2.urlopen(req, data=post_data)

        response = json.loads(utils.checkStr(r.read()))

        agg = response.get("agg","")
        if agg:
            titoli = agg.get("titoli","")
            if titoli:
                cards = titoli.get("cards",[])
                if cards:
                    s = cards
                    xbmc.log(str(cards),xbmc.LOGINFO)

        return s

    def getLastContentByTag(self, tags="", numContents=16):
        try: 
            tags = urllib.quote(tags)
        except: 
            tags = urllib.parse.quote(tags)
        
        domain = "RaiTv"
        #xsl = "rai_tv-statistiche-raiplay-json"
        xsl = "rai_tv-statistiche-portaleradio-nuovo-formato-immagine-json"
        
        url = self.baseUrl +  "/StatisticheProxy/proxyPost.jsp?action=getLastContentByTag&numContents=%s&tags=%s&domain=%s&xsl=%s" % \
              (str(numContents), tags, domain, xsl)

        xbmc.log("Raiplay.Search.getLastContentByTag url: " + url)

        data = urllib2.urlopen(url).read()
        data = utils.checkStr(data)
        try:
            response = json.loads(data)
            return response["list"]
        except:
            xbmc.log(data)
            return {}
