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



class COX():  
  
    def __init__(self):
        self.REFERER_URL = ''
        self.TARGET = ''
        self.ON_SUCCESS = ''
        self.ON_FAILURE = ''


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

        #First Redirect url
        '''
        https://idm.east.cox.net/affwebservices/public/saml2sso?SAMLRequest=lVNNj5swEL33VyDfDYGQlliBVbrpqpG2LU3YHnqpDAyNJbCpx2STf18DSTfd1aaq5NNo3sfMGy9uDk3t7EGjUDImvjshDshClUL%2BjMlDdkcjcpO8WSBv6qBly87s5AZ%2BdYDGWSKCNhZ3qyR2Degt6L0o4GFzH5OdMS0yz8PW5Rbk8lLl4BaqsRWvZ%2FO2y0%2F3LyiIs7LUQnIz%2BDmziLJxgaOxBAdXgmFhOPV4VT1CjqMoem2X16IYuANERZw7pQsYHMek4jUCcdarmPwoSj%2F05%2Fwdzblf0TCMfDqHgNNplJezyJ%2B%2FnUWVbcWUI4o9PIERO1hLNFyamAQTf0YnEZ36mR%2BxcGKfO4%2Bm34mTamVUoer3Qo5r7LRkiqNAJnkDyEzB%2BuFZ4E5YPjYh%2B5hlKU2%2FbDPifDvHEfRx2IAksjGA61ztSZgkY15scKwvGa4T8HMcJPmTn0W5L0NUkuaw43VFVeXJvMBWaYML71I3OV%2FNh4MB2U%2BEycLsdGuObAMWIctMncyN5dfdnUdjcDC2WeiStlyb47%2BMLrzngsnJ5N%2B2TqXPVnS9SpU9pKOzrGv1eKuBG3sDRncwnFTDzfUl9hVR0mpoZUZzqwHSEGeb9vRfO16LSoC%2B%2BCP%2Fs2PiPU1w%2BR2T3w%3D%3D&RelayState=_1de361bf-83fb-4f72-a0ad-3491cb2f12ce&SigAlg=http%3A%2F%2Fwww.w3.org%2F2000%2F09%2Fxmldsig%23rsa-sha1&Signature=F6Rh1sOZ2%2FknoXQYJ6JMLQwZRO5GDSAcXF5wD28uCnaLf4sEo0vflx6bqyux3wPNzzXGBVOIyh6bBEoCJATsl6COZrB4SB9jLkLGosIWYBctg6luq2O%2FQwqQbcv5UfzNdUoqh1KyrEtoamM8cav6pMqiY9GKrUbNE1EDNzrIFLC7XwcTq0pMcpiRoMt8TWLnP9dNtiLspv2CJW5c2GmzVAIrOUyURIBPsv5y5nYIILfgGRmJ9YoAY57zDxAw0cWqY401UQcQQ6S3GUnN3gdDcbO0eJPl%2BVFA6d6eUuMLNkNz6UGCzgZxgg%2FFUKYnB43uhUnnz%2BrIJmrIScrOD9NgKw%3D%3D HTTP/1.1
        Host: idm.east.cox.net
        Connection: keep-alive
        Proxy-Connection: keep-alive
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
        User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143
        Accept-Language: en-us
        Referer: https://sp.auth.adobe.com//adobe-services/1.0/authenticate/saml?domain_name=adobe.com&noflash=true&mso_id=Cox&requestor_id=nbcsports&no_iframe=true&client_type=iOS&client_version=1.9&redirect_url=http://adobepass.ios.app/
        Accept-Encoding: gzip, deflate
        '''
        
        url = FIND(idp_source,'"0;url=','"')
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)) 
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE),
                            ("Referer", IDP_URL)]
        
        resp = opener.open(url)
        login_source = resp.read()
        resp.close()        

        SAVE_COOKIE(cj)

        login_source = login_source.replace('\n',"")        

        print "RESP.GETURL() ==="        
        #print HTMLParser.HTMLParser().unescape(resp.geturl())
        self.REFERER_URL = resp.geturl()

        last_url = urllib.unquote(resp.geturl())
        last_url = last_url.replace('-','')
        print last_url
        
        saml_request = FIND(last_url,'SAMLRequest=','&')
        print "SAML REQUEST"
        print saml_request

        relay_state = FIND(last_url,'RelayState=','&')
        print "RELAY STATE"
        print relay_state

        saml_submit_url = FIND(login_source,'action="','"')

        self.TARGET = FIND(login_source,'<input type="hidden" name="target" value="','"')
        self.ON_SUCCESS = FIND(login_source,'<input type="hidden" name="onsuccess" value="','"')
        self.ON_FAILURE = FIND(login_source,'<input type="hidden" name="onfailure" value="','"')


        return saml_request, relay_state, saml_submit_url
    
    def LOGIN(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post username and password to idp        
        ###################################################################        
        
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            #("Origin", "https://ids.rr.com"),
                            ("Referer", self.REFERER_URL),
                            ("User-Agent", UA_IPHONE)]

        
        login_data = urllib.urlencode({'username' : USERNAME,
                                       'password' : PASSWORD,
                                       'CallerID' : 'tvonline',
                                       'x' :  '82',
                                       'y' :  '13',
                                       'target' :  self.TARGET,
                                       'onsuccess' :  self.ON_SUCCESS,
                                       'onfailure' :  self.ON_FAILURE,                                       
                                       'DeviceID' :  ''
                                       })
        
        try:
            resp = opener.open(saml_submit_url, login_data)
            print resp.getcode()
            print resp.info()
            #idp_source = resp.read()
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                idp_source = f.read()
            else:
                idp_source = resp.read()
                
            resp.close()
            
            saml_response = FIND(idp_source,'<input type="hidden" name="SAMLResponse" value="','"')  
            saml_response = HTMLParser.HTMLParser().unescape(saml_response)                                                        
            relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

            #Set Global header fields         
            #ORIGIN = 'https://idm.east.cox.net'
            #REFERER = 'https://idm.east.cox.net/affwebservices/public/saml2sso?SMASSERTIONREF=QUERY&RelayState=_1de361bf-83fb-4f72-a0ad-3491cb2f12ce&SAMLRequest=lVNNj5swEL33VyDfDYGQlliBVbrpqpG2LU3YHnqpDAyNJbCpx2STf18DSTfd1aaq5NNo3sfMGy9uDk3t7EGjUDImvjshDshClUL%2BjMlDdkcjcpO8WSBv6qBly87s5AZ%2BdYDGWSKCNhZ3qyR2Degt6L0o4GFzH5OdMS0yz8PW5Rbk8lLl4BaqsRWvZ%2FO2y0%2F3LyiIs7LUQnIz%2BDmziLJxgaOxBAdXgmFhOPV4VT1CjqMoem2X16IYuANERZw7pQsYHMek4jUCcdarmPwoSj%2F05%2Fwdzblf0TCMfDqHgNNplJezyJ%2B%2FnUWVbcWUI4o9PIERO1hLNFyamAQTf0YnEZ36mR%2BxcGKfO4%2Bm34mTamVUoer3Qo5r7LRkiqNAJnkDyEzB%2BuFZ4E5YPjYh%2B5hlKU2%2FbDPifDvHEfRx2IAksjGA61ztSZgkY15scKwvGa4T8HMcJPmTn0W5L0NUkuaw43VFVeXJvMBWaYML71I3OV%2FNh4MB2U%2BEycLsdGuObAMWIctMncyN5dfdnUdjcDC2WeiStlyb47%2BMLrzngsnJ5N%2B2TqXPVnS9SpU9pKOzrGv1eKuBG3sDRncwnFTDzfUl9hVR0mpoZUZzqwHSEGeb9vRfO16LSoC%2B%2BCP%2Fs2PiPU1w%2BR2T3w%3D%3D&SigAlg=http%3A%2F%2Fwww.w3.org%2F2000%2F09%2Fxmldsig%23rsa-sha1&Signature=F6Rh1sOZ2%2FknoXQYJ6JMLQwZRO5GDSAcXF5wD28uCnaLf4sEo0vflx6bqyux3wPNzzXGBVOIyh6bBEoCJATsl6COZrB4SB9jLkLGosIWYBctg6luq2O%2FQwqQbcv5UfzNdUoqh1KyrEtoamM8cav6pMqiY9GKrUbNE1EDNzrIFLC7XwcTq0pMcpiRoMt8TWLnP9dNtiLspv2CJW5c2GmzVAIrOUyURIBPsv5y5nYIILfgGRmJ9YoAY57zDxAw0cWqY401UQcQQ6S3GUnN3gdDcbO0eJPl%2BVFA6d6eUuMLNkNz6UGCzgZxgg%2FFUKYnB43uhUnnz%2BrIJmrIScrOD9NgKw%3D%3D'
        except:
            saml_response = ""
            relay_state = ""
        
        return saml_response, relay_state
