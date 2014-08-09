# -*- coding: utf-8 -*-
import urllib2
import json
from operator import itemgetter
from xml.dom import minidom

class OnDemand:
    baseUrl = "http://www.rai.tv"
    nothumb = "http://www.rai.tv/dl/RaiTV/2012/images/NoAnteprimaItem.png"

    editori = {"Rai1": "RaiUno", "Rai2": "RaiDue", "Rai3": "RaiTre",
               "Rai4": "Rai4", "Rai5": "Rai5", "Rai Gulp": "RaiGulp",
               "Rai Yoyo": "RaiYoYo", "Rai Movie": "RaiMovie",
               "Rai Fiction": "RaiFiction", "Rai Edu": "RaiEducational",
               "Rai Sport": "RaiSport", "Rai Internazionale": "RaiInternational",
               "Radio1": "Radio1", "Radio2": "Radio2", "Radio3": "Radio3",
               "Wr6": "WebRadio 6", "Wr7": "WebRadio 7", "Wr8": "WebRadio 8"}

    tematiche = ["Attualità", "Bianco e Nero", "Cinema", "Comici", "Cronaca", "Cucina", "Cultura", "Cultura e Spettacoli", "Economia", "Fiction",
        "Hi tech", "Inchieste", "Incontra", "Interviste", "Istituzioni", "Junior", "Moda", "Musica", "News", "Politica", "Promo", "Reality",
        "Salute", "Satira", "Scienza", "Società", "Spettacolo", "Sport", "Storia", "Telefilm", "Tempo libero", "Viaggi"]
    
    def getProgrammeList(self):
        url = "http://www.rai.tv/dl/RaiTV/programmi/ricerca/ContentSet-6445de64-d321-476c-a890-ae4ed32c729e-darivedere.html"
        response = json.load(urllib2.urlopen(url))
        return response

    def searchByIndex(self, index):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["index"] == index and programme["nascosto"] == "false":
                result.append(programme)
        return result

    def searchByName(self, name):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["title"].lower().find(name) != -1 and programme["nascosto"] == "false":
                result.append(programme)
        return result

    def searchByChannel(self, channel):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["editore"] == channel and programme["nascosto"] == "false":
                result.append(programme)
        return result

    def searchByTheme(self, theme):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if theme in programme["tematiche"] and programme["nascosto"] == "false":
                result.append(programme)
        return result

    def searchNewProgrammes(self):
        programmes = self.getProgrammeList()
        programmes = sorted(programmes, key = itemgetter("date"), reverse = True)
        result = []
        for programme in programmes:
            if programme["nascosto"] == "false":
                result.append(programme)
            if len(result) == 10:
                break
        return result

    def getProgrammeSets(self, path):
        # get XML url
        url = self.baseUrl + path
        url = url.replace("/dl/RaiTV/programmi/page/", "/dl/RaiTV/programmi/")
        url = url.replace(".html", ".xml")
        print "Program URL: %s" % url

        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)
        
        # TODO: blocks are not handled
        programmeSets = []
        for node in dom.getElementsByTagName('set'):
            name = node.attributes["name"].value
            uniquename = node.attributes["uniquename"].value
            try:
                types = node.getElementsByTagName('Summary')[0].getElementsByTagName('TypeOccurrency')
            except IndexError:
                types = []

            for typeoccurrency in types:
                # TODO: handle more than one media type
                # therefore programmeSet["mediatype"] must be a list
                mediatype = typeoccurrency.attributes["type"].value
                occurrency = typeoccurrency.attributes["occurrency"].value

                programmeSet = {}
                programmeSet["name"] = name
                programmeSet["uniquename"] =  uniquename
                    
                if mediatype == "RaiTv Media Video Item" and int(occurrency) > 0:
                    programmeSet["mediatype"] = "V"
                    programmeSets.append(programmeSet)
                elif mediatype == "RaiTv Media Audio Item" and int(occurrency) > 0:
                    programmeSet["mediatype"] = "A"
                    programmeSets.append(programmeSet)
                elif mediatype == "RaiTv Media Podcast Item" and int(occurrency) > 0:
                    programmeSet["mediatype"] = "P"
                    programmeSets.append(programmeSet)

        return programmeSets

    def getItems(self, uniquename, mediatype):
        items = []
        page = 0
        
        while True:
            url = "http://www.rai.tv/dl/RaiTV/programmi/json/liste/%s-json-%s-%s.html" % (uniquename, mediatype, page)
            print "Item URL: %s" % url
            response = json.load(urllib2.urlopen(url))
            
            items = items + response["list"]
            
            page = page + 1
            if page == int(response["pages"]):
                break

        return items
        
    def getMediaUrl(self, uniquename):
        url = "http://www.rai.tv/dl/RaiTV/programmi/media/%s.html?json" % uniquename
        print "Media URL: %s" % url
        response = json.load(urllib2.urlopen(url))
        
        mediaUrl = ""
        mediatype = response["type"]
        
        if mediatype == "RaiTv Media Video Item":
            if response["h264"] != "":
                mediaUrl = response["h264"]
            elif "wmv" in response and response["wmv"] != "":
                mediaUrl = response["wmv"]
            else:
                mediaUrl = response["mediaUri"]
        else:
            # No media URL for audio and podcasts in json
            url = "http://www.rai.tv/dl/RaiTV/programmi/media/%s.xml" % uniquename
            print "Media URL: %s" % url
            xmldata = urllib2.urlopen(url).read()
            dom = minidom.parseString(xmldata)
            
            if mediatype == "RaiTv Media Audio Item":
                audioUnit = dom.getElementsByTagName('audioUnit')
                mediaUrl = audioUnit[0].getElementsByTagName('url')[0].childNodes[0].data
            elif mediatype == "RaiTv Media Podcast Item":
                linkUnit  = dom.getElementsByTagName('linkUnit')
                mediaUrl = linkUnit[0].getElementsByTagName('link')[0].childNodes[0].data

        return mediaUrl, mediatype
