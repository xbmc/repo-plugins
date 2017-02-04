# -*- coding: utf-8 -*-
import urllib2
import json

class RadioRai:
    def getChannels(self):
        url = "http://rai.it/dl/portaleRadio/popup/ContentSet-003728e4-db46-4df8-83ff-606426c0b3f5-json.html"
        response = json.load(urllib2.urlopen(url))
        return response["dati"]
