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



class CHARTER():    

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

        saml_request = FIND(idp_source,'<input type="hidden" name="SAMLRequest" value="','"')
        #print saml_request

        relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        saml_submit_url = FIND(idp_source,'action="','"')
        
        
        print saml_submit_url
        #print relay_state
        return saml_request, relay_state, saml_submit_url
    
    def LOGIN(self, saml_request, relay_state, saml_submit_url):
        ###################################################################
        #Post SAML Request & Relay State to get required cookies
        ###################################################################       

        url = 'https://idp.aws.charter.net/openam/SSOPOST/metaAlias/charter/idp'
        #cj = cookielib.LWPCookieJar()
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
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

        
        data = urllib.urlencode({'SAMLRequest' : saml_request,
                                   'RelayState' : relay_state
                                   })
        
        
        resp = opener.open(url, data)
        print resp.getcode()
        print resp.info()
        print "URL"
        print resp.geturl()
        #idp_source = resp.read()
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            idp_source = f.read()
        else:
            idp_source = resp.read()
            
        resp.close()
        SAVE_COOKIE(cj)        
        
        goto = FIND(idp_source,'<input type="hidden" name="goto" value="','"')            
        sun_query = FIND(idp_source,'<input type="hidden" name="SunQueryParamsString" value="','"')
        requestor_id = FIND(idp_source,'<input type="hidden" name="requestorID" value="','"')
    
        ###################################################################
        #Post username and password to idp        
        ###################################################################
        
        #Add additional cookies
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        ck = cookielib.Cookie(version=0, name='user', value=USERNAME, port=None, port_specified=False, domain='.charter.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)        
        ck = cookielib.Cookie(version=0, name='s_cc', value='true', port=None, port_specified=False, domain='.charter.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)        
        s_fid = ''.join([random.choice('0123456789ABCDEF') for x in range(16)])+'-'+''.join([random.choice('0123456789ABCDEF') for x in range(16)])
        ck = cookielib.Cookie(version=0, name='s_fid', value=s_fid, port=None, port_specified=False, domain='.charter.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        ck = cookielib.Cookie(version=0, name='s_sq', value='%5B%5BB%5D%5D', port=None, port_specified=False, domain='.charter.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        SAVE_COOKIE(cj)

        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        url = 'https://idp.aws.charter.net/openam/UI/Login'        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://idp.aws.charter.net"),
                            ("Referer", "https://idp.aws.charter.net/openam/SSOPOST/metaAlias/charter/idp"),
                            ("User-Agent", "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143")]

        
        login_data = urllib.urlencode({'IDToken1' : USERNAME,
                                       'IDToken2' : PASSWORD,
                                       'rememberMe' : 'on',
                                       'IDButton' : ' Log In ',
                                       'goto' : goto,
                                       'SunQueryParamsString' : sun_query,
                                       'encoded' : 'true',
                                       'requestorID' : requestor_id,
                                       'referer' : IDP_URL,
                                       'gx_charset' : 'UTF-8'
                                       })
        
        try:
            resp = opener.open(url, login_data)
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
            #saml_response = saml_response.replace('&#xd;&#xa;','')
            saml_response = HTMLParser.HTMLParser().unescape(saml_response)        
            #saml_response = urllib.quote(saml_response)


            relay_state = FIND(idp_source,'<input type="hidden" name="RelayState" value="','"')

        except:
            saml_response = ""
            relay_state = ""
        #Set Global header fields         
        global ORIGIN
        global REFERER
        ORIGIN = 'https://idp.aws.charter.net'
        REFERER = 'https://idp.aws.charter.net/openam/UI/Login'

        print saml_response
        return saml_response, relay_state
