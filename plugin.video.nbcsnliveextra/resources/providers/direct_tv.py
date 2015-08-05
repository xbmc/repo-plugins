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



class DIRECT_TV():    

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
        print resp.info()
        idp_source = resp.read()
        resp.close()
        #print idp_source
        SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        

        saml_request = FIND(idp_source,'<input type="hidden" name="SAMLRequest" value="','"')
        #print saml_request

        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        saml_submit_url = FIND(idp_source,'action="','"')
        
        
        print saml_submit_url
        print relay_state
        print saml_request
        
        return saml_request, relay_state, saml_submit_url

    
    def LOGIN(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post username and password to idp        
        ###################################################################
        #url = 'https://ids.rr.com/nidp/saml2/sso?sid=0'
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://sp.auth.adobe.com"),
                            ("Referer", IDP_URL),
                            ("User-Agent", UA_IPHONE)]

        
        login_data = urllib.urlencode({'SAMLRequest' : saml_request,
                                       'RelayState' : relay_state
                                       })
        
        try:
            resp = opener.open(saml_submit_url, login_data)
            print resp.info()
            #idp_source = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                idp_source = f.read()           
            else:
                idp_source = resp.read()
                
            resp.close()
            
            last_url = resp.geturl()
            next_url = FIND(idp_source,'action="','"')

            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                ("Accept-Encoding", "gzip, deflate"),
                                ("Accept-Language", "en-us"),
                                ("Content-Type", "application/x-www-form-urlencoded"),                            
                                ("Connection", "keep-alive"),
                                ("Origin", "https://idp.dtvce.com"),
                                ("Referer", last_url),
                                ("User-Agent", UA_IPHONE)]

            
            login_data = urllib.urlencode({'username' : USERNAME,
                                           'password' : PASSWORD,
                                           'register' : 'on'
                                           })
            
            resp = opener.open(next_url, login_data)
            idp_source = resp.read()
            resp.close()

            saml_response = FIND(idp_source,'<input type="hidden" name="SAMLResponse" value="','"')
            relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

            
            #Set Global header fields         
            ORIGIN = 'https://idp.dtvce.com'
            #REFERER = 'https://idp.dtvce.com/dtv-idp-authn/login?stateInfo=eJwFwdmiQkAAANAP8oCawkMPsszFYCxje4vGHkKFr7%2FnqJzcprUy8wDcCsa%2BetmjwFP7mf98NLuJYz85K3ftiCPVviHz9MTH6odVSyEnIWOFdyNh6k80CjuL3ZiOXxeeXOZrIYlfBnIizjOuzWFWIezjIPFzGMebq3fMXKSeTpqWBatFg%2FISyB19w4lc5LrAfHBdmmVXgHEPjkwQg4SCpkwFTFWY8XqFJ5xkp1cFSsbzmOw1F99Mezf2gkQ6XjtFZDvk0a8q9drxq821F0vSDhvD%2FKRie%2BdnhZw1W4ys%2BP4BTSxHyFIPHH%2Fo2UHj6hcT76YHiFz96Pp8X%2FBQSQLkseSJjqzMT4LCFJiJ%2FLAIeyyiOoxKG7RIy8c%2BxKHnGZsp3%2F4BemFx8A%3D%3D&providerName=IDP_NBCSports_C01'
            REFERER = resp.geturl()
        except:
            saml_response = ""
            relay_state = ""
            
        
        return saml_response, relay_state
        

