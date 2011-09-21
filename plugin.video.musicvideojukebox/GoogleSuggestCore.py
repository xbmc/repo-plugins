# coding: utf-8
'''
Created on 18 sep 2011

@author: Emuller
'''
import os,sys
import urllib,urllib2,re
import string
from xml.dom import minidom

import iZECore 

izecore = iZECore.iZECore()

class GoogleSuggestCore(object):
    
    def search(self, q):        
        url = "http://suggestqueries.google.com/complete/search?hl=en&ds=yt&output=toolbar&q=%s" % urllib.quote_plus(q)
        
        xmldoc = izecore.getXmlResponse(url)
        
        ''' get the first item '''
        suggestions = xmldoc.getElementsByTagName("CompleteSuggestion")
        if suggestions.length>0:
            firstitem = suggestions[0]
            data = firstitem.getElementsByTagName("suggestion")[0].getAttribute('data')
        else:
            data = q
        
        return data