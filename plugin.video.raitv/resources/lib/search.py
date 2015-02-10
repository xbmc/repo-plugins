# -*- coding: utf-8 -*-
import json
import urllib
import urllib2

class Search:
    _baseurl = "http://www.rai.tv"
    _nothumb = "http://www.rai.tv/dl/RaiTV/2012/images/NoAnteprimaItem.png"
    
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

    def searchText(self, text="", numContents=36):
        # ordina per rilevanza (default su sito web)
        sort="date:D:L:d1"
        # ordina per data (default su app android)
        #sort="date:D:S:d1"
        
        url = "http://www.ricerca.rai.it/search?site=raitv&output=xml_no_dtd&proxystylesheet=json&client=json&sort=%s&filter=0&getfields=*&partialfields=videourl&num=%s&q=%s" % (sort, numContents, urllib.quote_plus(text))
        print "Search URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        return response["list"]
    
    def getLastContentByTag(self, tags="", numContents=16):
        tags = urllib.quote(tags)
        domain = "RaiTv"
        
        url = "http://www.rai.tv/StatisticheProxy/proxyPost.jsp?action=getLastContentByTag&numContents=%s&tags=%s&domain=%s&xsl=rai_tv-statistiche-json" % \
              (str(numContents), tags, domain)
        print "Search URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        return response["list"]
    
    def getMostVisited(self, tags, days=7, numContents=16):
        tags = urllib.quote(tags)
        domain = "RaiTv"
        
        url = "http://www.rai.tv/StatisticheProxy/proxyPost.jsp?action=mostVisited&days=%s&state=1&records=%s&tags=%s&domain=%s%xsl=rai_tv-statistiche-json" % \
            (str(days), str(numContents), tags, domain)
        print "Search URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        return response["list"]

    def getContent(self, itemId):
        domain = "RaiTv"
        
        url = "http://www.rai.tv/StatisticheProxy/proxy.jsp?action=getContent&domain=%s&xsl=rai_tv-statistiche-json&localId=%s" % \
            (domain, itemId)
        print "Search URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        return response["list"][0]
