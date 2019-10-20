# -*- coding: utf-8 -*-
import json
import urllib
try:
  import urllib.request as urllib2
except ImportError:
    import urllib2

class Search:
    baseUrl = "http://www.rai.it"

    newsArchives = {"TG1": "NomeProgramma:TG1^Tematica:Edizioni integrali",
        "TG2": "NomeProgramma:TG2^Tematica:Edizione integrale",
        "TG3": "NomeProgramma:TG3^Tematica:Edizioni del TG3"}
    
    newsProviders = {"TG1": "Tematica:TG1",
        "TG2": "Tematica:TG2",
        "TG3": "Tematica:TG3",
        "Rai News": "Tematica:Rai News",
        "Rai Sport": "Tematica:spt",
        "Rai Parlamento": "PageOB:Page-f3f817b3-1d55-4e99-8c36-464cea859189"}

    tematiche = ["Attualità", "Bianco e Nero", "Cinema", "Comici", "Cronaca", "Cucina", "Cultura", "Cultura e Spettacoli", "Economia", "Fiction",
        "Hi tech", "Inchieste", "Incontra", "Interviste", "Istituzioni", "Junior", "Moda", "Musica", "News", "Politica", "Promo", "Reality",
        "Salute", "Satira", "Scienza", "Società", "Spettacolo", "Sport", "Storia", "Telefilm", "Tempo libero", "Viaggi"]
    
    def getLastContentByTag(self, tags="", numContents=16):
        try: tags = urllib.quote(tags)
        except: tags = urllib.parse.quote(tags)
        domain = "RaiTv"
        xsl = "rai_tv-statistiche-raiplay-json"
        
        url = self.baseUrl +  "/StatisticheProxy/proxyPost.jsp?action=getLastContentByTag&numContents=%s&tags=%s&domain=%s&xsl=%s" % \
              (str(numContents), tags, domain, xsl)
        response = json.load(urllib2.urlopen(url))
        return response["list"]
    
    def getMostVisited(self, tags, days=7, numContents=16):
        try: tags = urllib.quote(tags)
        except: tags = urllib.parse.quote(tags)
        domain = "RaiTv"
        xsl = "rai_tv-statistiche-raiplay-json"
        
        url = self.baseUrl +  "/StatisticheProxy/proxyPost.jsp?action=mostVisited&days=%s&state=1&records=%s&tags=%s&domain=%s&xsl=%s" % \
            (str(days), str(numContents), tags, domain, xsl)
        response = json.load(urllib2.urlopen(url))
        return response["list"]
