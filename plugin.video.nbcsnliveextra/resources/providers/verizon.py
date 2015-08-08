import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import time
import cookielib
import base64
import string, random
from resources.globals import *



class VERIZON():    

    def GET_IDP(self):        
        if not os.path.exists(ADDON_PATH_PROFILE):
            os.makedirs(ADDON_PATH_PROFILE)
        

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        
        #IDP_URL= 'https://sp.auth.adobe.com/adobe-services/authenticate?requestor_id=nbcsports&redirect_url=http://stream.nbcsports.com/nbcsn/index_nbcsn-generic.html?referrer=http://stream.nbcsports.com/liveextra/&domain_name=stream.nbcsports.com&mso_id=TWC&noflash=true&no_iframe=true'
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(IDP_URL)
        idp_source = resp.read()
        resp.close()
        #print idp_source
        #cj.save(ignore_discard=True);                
        SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        
        redirect_url = FIND(idp_source,'<meta http-equiv="refresh" content="0;url=','"')


        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(redirect_url)
        idp_source = resp.read()
        resp.close()
        #SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        
        #<input type="hidden" name="amLoginUrl" value="
        am_login_url = FIND(idp_source,'<input type="hidden" name="amLoginUrl" value="','"')        

        
        return None, None, am_login_url
    
    def LOGIN(self, blank_1, blank_2, am_login_url):        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-US,en;q=0.8"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        
        body = urllib.urlencode({'cookiedomain' : '.verizon.com',
                               'amLoginUrl' : am_login_url,
                               'stid' : 'off',
                               'forceprofile' : 'off',
                               'seclock':'off',
                               'vzw':'off',
                               'IDToken1': USERNAME,
                               'IDToken2': PASSWORD
                               })

        resp = opener.open(am_login_url, body)
        idp_source = resp.read()
        resp.close()
        #SAVE_COOKIE(cj)
        print resp.getcode()
        print resp.info()
        print "URL"
        referer_url = resp.geturl()

        sign_in_url = FIND(idp_source,'xmlHttp.open("POST", "','"')
        print "SIGN IN URL"
        print sign_in_url

        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "*/*"),
                            ("Accept-Language", "en-US,en;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://signin.verizon.com"),
                            ("Referer", referer_url),
                            ("Content-Type", "text/xml"),                            
                            ("User-Agent", UA_IPHONE)]
        
        body = urllib.urlencode({})

        resp = opener.open(sign_in_url, body)
        json_source = json.load(resp)
        resp.close()
        SAVE_COOKIE(cj)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        
                
        saml_response = json_source['SAMLResponse']
        print saml_response
        
        relay_state = json_source['RelayState']
        print relay_state
         
        #Set Global header fields         
        global ORIGIN
        global REFERER
        ORIGIN = 'https://signin.verizon.com'
        REFERER = referer_url

        print saml_response
        return saml_response, relay_state
