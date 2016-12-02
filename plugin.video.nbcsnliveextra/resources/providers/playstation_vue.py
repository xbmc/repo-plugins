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



class PLAYSTATION_VUE(): 


    def GET_IDP(self):        
        if not os.path.exists(ADDON_PATH_PROFILE):
            os.makedirs(ADDON_PATH_PROFILE)
        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))                
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),                            
                            ("Connection", "keep-alive"),
                            ("Accept-Encoding", "deflate"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(IDP_URL)
        idp_source = resp.read()
        resp.close()
        #print idp_source
        #cj.save(ignore_discard=True);                
        SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        

        saml_request = FIND(idp_source,'<input type="hidden" name="SAMLRequest" value="','"')
        #print saml_request

        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        saml_submit_url = FIND(idp_source,'action="','"')
        
        
        print saml_submit_url
        #print relay_state
        return saml_request, relay_state, saml_submit_url
    
    def LOGIN(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post SAML Request & Relay State to get requestId
        ###################################################################       

        url = 'https://adobe.auth-gateway.net/saml/saml2/idp/SSOService.php'

        #cj = cookielib.LWPCookieJar()
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),
                            ("Origin", "https://sp.auth.adobe.com"),
                            ("Referer", IDP_URL),
                            ("User-Agent", UA_IPHONE)]

        
        data = urllib.urlencode({'SAMLRequest' : saml_request,
                                   'RelayState' : relay_state
                                   })
        
        
        resp = opener.open(url, data)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        last_url = resp.geturl()
        idp_source = resp.read()
        resp.close()
        SAVE_COOKIE(cj)        
        

        #cj = cookielib.LWPCookieJar()
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),
                            ("Origin", "https://sp.auth.adobe.com"),
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]

        


        
        resp = opener.open(last_url+"&history=1")
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        last_url = resp.geturl()
        idp_source = resp.read()
        resp.close()
        SAVE_COOKIE(cj)  



        #######################################################
        # firstbookend
        #######################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]

        
        resp = opener.open(last_url+"&history=1")
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        idp_source = resp.read()
        resp.close()
        SAVE_COOKIE(cj) 

     

        #request_id = FIND(idp_source,'<input type="hidden" name="requestId" value="','"')
        params = FIND(idp_source,'<input id="brandingParams" type="hidden" name="params" value="','"')



    
        ###################################################################
        #Post username and password       
        ###################################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        url = 'https://auth.api.sonyentertainmentnetwork.com/login.do'        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),
                            ("Origin", "https://auth.api.sonyentertainmentnetwork.com"),
                            ("Referer", "https://auth.api.sonyentertainmentnetwork.com/login.jsp?service_entity=psn&mid=nbcsports&request_theme=liquid"),
                            ("User-Agent", UA_IPHONE)]

        
        login_data = urllib.urlencode({'params' : params,
                                       'j_username' : USERNAME,
                                       'j_password' : PASSWORD
                                     })
        
        #try:
        resp = opener.open(url, login_data)
        print resp.getcode()
        print resp.info()
        idp_source = resp.read()            
        resp.close()
        SAVE_COOKIE(cj) 

        url = FIND(idp_source,'<meta http-equiv="refresh" content="0;url=','"')

        #######################################################
        # sony DiscoveryAssociationsResume
        #######################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]

        
        resp = opener.open(url)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        idp_source = resp.read()
        last_url = resp.geturl()
        resp.close()
        SAVE_COOKIE(cj) 


        #######################################################
        # sony lastbookend
        #######################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]
        

        resp = opener.open(last_url+"&history=3")
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()            
        idp_source = resp.read()
        last_url = resp.geturl()
        resp.close()
        SAVE_COOKIE(cj) 

        saml_response = FIND(idp_source,'<input type="hidden" name="SAMLResponse" value="','"') 
        saml_response = HTMLParser.HTMLParser().unescape(saml_response)        
        url = FIND(idp_source,'<form method="post" action="','"')
       
        #except:
        #saml_response = ""
        #relay_state = ""

        #######################################################
        # adobe saml module.php
        #######################################################
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]
        

        data = urllib.urlencode({'SAMLResponse' : saml_response})

        resp = opener.open(url,data)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()            
        idp_source = resp.read()
        last_url = resp.geturl()
        resp.close()
        SAVE_COOKIE(cj) 



        url = FIND(idp_source,'<meta http-equiv="refresh" content="0;url=','"')

        #######################################################
        # adobe DiscoveryAssociationsResume
        #######################################################
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]
        

        resp = opener.open(url)        
        idp_source = resp.read()
        last_url = resp.geturl()
        resp.close()
        SAVE_COOKIE(cj) 


        #######################################################
        # adobe lastbookend
        #######################################################

        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                            
                            ("Connection", "keep-alive"),                            
                            ("Referer", last_url),
                            ("User-Agent", UA_IPHONE)]
        

        resp = opener.open(last_url+"&history=4")
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()            
        idp_source = resp.read()
        last_url = resp.geturl()
        resp.close()
        SAVE_COOKIE(cj) 


        saml_response = FIND(idp_source,'<input type="hidden" name="SAMLResponse" value="','"') 
        saml_response = HTMLParser.HTMLParser().unescape(saml_response)        
        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')
        #Set Global header fields         
        global ORIGIN
        global REFERER

        ORIGIN = 'https://adobe.auth-gateway.net'        
        REFERER = last_url
        print saml_response

        return saml_response, relay_state

