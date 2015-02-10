import urllib
import urllib2
import re
import os
import json

def get_url(url, isJson=False):
    responseData = JsonGetURL(url)
    if isJson: 
        responseJson = json.loads(responseData)
        return responseJson
        
    return responseData

def JsonGetURL(Url):
    req = urllib2.Request(Url, None, {'Content-Type': 'application/json'})
    try:
        u = urllib2.urlopen(req)
    except urllib2.URLError, e:
        if e.code == 404:
            resp = '{"status": "0"}'
    else:
        resp = u.read()
        u.close()

    return resp