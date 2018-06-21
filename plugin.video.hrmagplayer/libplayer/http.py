#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, urllib2

class HttpRetriever:
    def __init__(self):
        self.baseurl = 'https://www.hr-fernsehen.de/sendungen-a-z/'
        self.resource = '/index.html'
        self.categoryurl = '/sendungen'
	
    def get(self, url):
        values = {}
        headers = {}

        data = urllib.urlencode(values)
        req = urllib2.Request(url, None)
        response = urllib2.urlopen(req)
        page = response.read()
        return page

    def getCategoryUrl(self, cid):
        return self.baseurl + cid + self.resource
    
    def getShowListUrl(self, cid):
        return self.baseurl + cid + self.categoryurl + self.resource
    

    
