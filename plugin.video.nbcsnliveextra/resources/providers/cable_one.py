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


class CABLE_ONE():    

    def LOGIN(self, saml_request, relay_state, saml_submit_url):            
        first_bookend_url = self.POST_SAML_REQUEST(saml_request, relay_state, saml_submit_url)                
        first_bookend_url_2 = self.FIRST_BOOKEND(first_bookend_url)      
        login_url = self.FIRST_BOOKEND(first_bookend_url_2)      
        saml_response, relay_state = self.SELF_LOGIN(login_url)        

        return saml_response, relay_state

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
        SAVE_COOKIE(cj)

        idp_source = idp_source.replace('\n',"")        

        saml_request = FIND(idp_source,'<input type="hidden" name="SAMLRequest" value="','"')
        #print saml_request

        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        saml_submit_url = FIND(idp_source,'action="','"')
        
        
        print saml_submit_url
        #print relay_state
        return saml_request, relay_state, saml_submit_url
   
    def POST_SAML_REQUEST(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post username and password to idp        
        ###################################################################                     
        #cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            #("Connection", "keep-alive"),
                            ("Origin", "https://sp.auth.adobe.com"),
                            ("Referer", IDP_URL),
                            ("User-Agent", UA_IPHONE)]

        
        login_data = urllib.urlencode({'SAMLRequest' : saml_request,
                                       'RelayState' : relay_state,                                       
                                       })
        
        resp = opener.open(saml_submit_url, login_data)
        resp.close()
        cj.save(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True);

        first_bookend_url = resp.geturl()+ "&history=1"

        return first_bookend_url
        
        

    def FIRST_BOOKEND(self,first_bookend_url):        
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),                                                        
                            ("Referer", first_bookend_url),
                            ("User-Agent", UA_IPHONE)]

        
        resp = opener.open(first_bookend_url)
        #idp_source = resp.read()
        print resp.geturl()
        print resp.info()
        #print resp.getcode()
        resp.close()
        #print idp_source
        #cj.save(ignore_discard=True);
        cj.save(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True);
        first_bookend_url = resp.geturl()+ "&history=1"

        return first_bookend_url
        

    
    def SELF_LOGIN(self,login_url):        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        
        ck = cookielib.Cookie(version=0, name='s_cc', value='true', port=None, port_specified=False, domain='identity1.dishnetwork.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        ck = cookielib.Cookie(version=0, name='s_sq', value='s_sq=synacortveauth%3D%2526pid%253DFederated%252520Login%2526pidt%253D1%2526oid%253Dauthsynacor_auth.cableone.net%2526oidt%253D3%2526ot%253DSUBMIT', port=None, port_specified=False, domain='identity1.dishnetwork.com', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        
       
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),                            
                            ("Referer", login_url),                                                     
                            ("User-Agent", UA_IPHONE)]


        
        login_data = urllib.urlencode({'username' : USERNAME,
                                       'password' : PASSWORD,                                                                         
                                       'source' : 'authsynacor_auth.cableone.net',
                                       'source_button' : 'authsynacor_auth.cableone.net'                                       
                                       })
       
       
        resp = opener.open(login_url,login_data)   
      
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            final_response = f.read()
        else:
            final_response = resp.read()
        
        resp.close()
        print "FINAL RESPONSE"
        print final_response
        last_url = resp.geturl()

        final_response = final_response.replace('\n',"")         
        discovery_url = FIND(final_response,'location.href = "','"')
        
        saml_response = ''
        relay_state = ''

        if 'captcha' in final_response:
            saml_response = 'captcha'

        

        if discovery_url != '':
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                ("Accept-Encoding", "gzip, deflate"),
                                ("Accept-Language", "en-us"),
                                ("Content-Type", "application/x-www-form-urlencoded"),
                                ("Proxy-Connection", "keep-alive"),
                                ("Connection", "keep-alive"),                            
                                ("Referer", last_url),                                
                                ("User-Agent", UA_IPHONE)]
           
            resp = opener.open(discovery_url)
            source = resp.read()
            print resp.geturl()
            last_url = resp.geturl()
            #print source
            resp.close()


            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                ("Accept-Encoding", "gzip, deflate"),
                                ("Accept-Language", "en-us"),
                                ("Content-Type", "application/x-www-form-urlencoded"),
                                ("Proxy-Connection", "keep-alive"),
                                ("Connection", "keep-alive"),                            
                                ("Referer", last_url),                                
                                ("User-Agent", UA_IPHONE)]
           
            
            resp = opener.open(last_url+"&history=3")
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                source = f.read()

            #source = resp.read()
            print resp.geturl()
            last_url = resp.geturl()
            print source
            resp.close()      


            saml_response = FIND(source,'<input type="hidden" name="SAMLResponse" value="','"')

          
            proxy_url = 'https://adobe.auth-gateway.net/saml/module.php/saml/sp/saml2-acs.php/proxy_auth.cableone.net'
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                ("Accept-Encoding", "gzip, deflate"),
                                ("Accept-Language", "en-us"),
                                ("Content-Type", "application/x-www-form-urlencoded"),
                                ("Proxy-Connection", "keep-alive"),
                                ("Connection", "keep-alive"),                            
                                ("Referer", last_url),    
                                ("User-Agent", UA_IPHONE)]
           
            body = urllib.urlencode({'SAMLResponse' : saml_response})

            resp = opener.open(proxy_url,body)
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                source = f.read()

            #source = resp.read()
            print resp.geturl()
            last_url = resp.geturl()
            print source
            resp.close()      

            discovery_url = FIND(source,'location.href = "','"')
            print discovery_url
            
            saml_response = ''
            relay_state = ''

            if 'captcha' in source:
                saml_response = 'captcha'

            

            if discovery_url != '':                
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
                opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                    ("Accept-Encoding", "gzip, deflate"),
                                    ("Accept-Language", "en-us"),
                                    ("Proxy-Connection", "keep-alive"),
                                    ("Connection", "keep-alive"),                            
                                    ("Referer", last_url),                                
                                    #("Cookie", cookies),
                                    ("User-Agent", UA_IPHONE)]
               
                resp = opener.open(discovery_url)
                source = resp.read()
                print resp.geturl()
                last_url = resp.geturl()
                #print source
                resp.close()


                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
                opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                                    ("Accept-Encoding", "gzip, deflate"),
                                    ("Accept-Language", "en-us"),
                                    ("Content-Type", "application/x-www-form-urlencoded"),
                                    ("Proxy-Connection", "keep-alive"),
                                    ("Connection", "keep-alive"),                            
                                    ("Referer", last_url),                                
                                    ("User-Agent", UA_IPHONE)]
               
                
                resp = opener.open(last_url+"&history=4")
                if resp.info().get('Content-Encoding') == 'gzip':
                    buf = StringIO(resp.read())
                    f = gzip.GzipFile(fileobj=buf)
                    source = f.read()

                #source = resp.read()
                print resp.geturl()
                last_url = resp.geturl()
                print source
                resp.close()      


                saml_response = FIND(source,'<input type="hidden" name="SAMLResponse" value="','"')
                relay_state = FIND(source,'<input type="hidden" name="RelayState" value="','"')

                #Set Global header fields         
                ORIGIN = 'https://adobe.auth-gateway.net'
                REFERER = last_url

                SAVE_COOKIE(cj)

        
        return saml_response, relay_state

        
