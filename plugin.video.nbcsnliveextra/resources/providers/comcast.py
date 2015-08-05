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



class COMCAST():    

    def GET_IDP(self):
        
        if not os.path.exists(ADDON_PATH_PROFILE):
            os.makedirs(ADDON_PATH_PROFILE)
        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(IDP_URL)
        idp_source = resp.read()
        resp.close()
        print idp_source
        print resp.geturl()        
        #cj.save(ignore_discard=True);                
        SAVE_COOKIE(cj)
        idp_source = idp_source.replace('\n',"")        
        
        url = FIND(idp_source,'content="0;url=','"')                
        

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Referer", "https://sp.auth.adobe.com//adobe-services/1.0/authenticate/saml?domain_name=adobe.com&noflash=true&mso_id=Comcast_SSO&requestor_id=nbcsports&no_iframe=true&client_type=iOS&client_version=1.9&redirect_url=http://adobepass.ios.app/"),
                            ("User-Agent", UA_IPHONE)]
        
        resp = opener.open(url)
        idp_source = resp.read()
        resp.close()
        #print "SOURCE"
        #print idp_source
        last_url = resp.geturl()        
        #print last_url

        #cj.save(ignore_discard=True);                
        SAVE_COOKIE(cj)
        
        self.GET_OAX_COOKIE()                
        self.GET_S_VI_COOKIE(last_url)
        
        req_id = FIND(resp.geturl(),'reqId=','&')        
        relay_state = ''
        not_used = ''
               
        return req_id, last_url, not_used
    
    def LOGIN(self, req_id, referer, not_used):
        ###################################################################
        #Post username and password to idp        
        ###################################################################               
        #print "MY REQ ID IS " + req_id

        url = 'https://login.comcast.net/login'
        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        ck = cookielib.Cookie(version=0, name='s_sq', value='comcastnet%3D%2526pid%253Dmobile%252520app%252520sign%252520in%2526pidt%253D1%2526oid%253DSIGN%252520IN%2526oidt%253D3%2526ot%253DSUBMIT', port=None, port_specified=False, domain='.comcast.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        SAVE_COOKIE(cj)

        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        continue_url = FIND(referer,'&continue=','&')
        continue_url = urllib.unquote(continue_url).decode('utf8') 
        #print continue_url
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Origin", "https://login.comcast.net"),
                            ("Referer", referer),
                            ("User-Agent", UA_IPHONE+' Mobile/12F70')]

        
        login_data = urllib.urlencode({'user' : USERNAME,
                                       'passwd' : PASSWORD,
                                       'reqId' : req_id,
                                       'pf_sp' : 'https://saml.sp.auth.adobe.com/on-behalf-of/nbcsports',
                                       'ipAddrAuthn':'false',
                                       'deviceAuthn':'false',
                                       's':'sso-pf',
                                       'forceAuthn':'false',
                                       'r':'comcast.net',
                                       'continue':continue_url,
                                       'passive':'false',
                                       'lang' : 'en'
                                       })

        try:
            resp = opener.open(url, login_data)
            print resp.getcode()
            print resp.info()        
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                response = f.read()           
            else:
                response = resp.read() 
            resp.close()
            SAVE_COOKIE(cj)
            
            
            saml_response = FIND(response,'<input type="hidden" name="SAMLResponse" value="','"')
            relay_state = FIND(response,'<input type="hidden" name="RelayState" value="','"')
            print "LOGIN RESPONSE--------------------------------------------------------------"
            print response                
            print "----------------------------------------------------------------------------"
            ORIGIN = 'https://login.comcast.net'        
            REFERER = resp.geturl()
        except:
            saml_response = ""
            relay_state = ""
        
        return saml_response, relay_state




    def GET_OAX_COOKIE(self):                
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        url = 'http://oascentral.comcast.net/RealMedia/ads/adstream_sx.ads/m.comcast.net/i/sign_in/1[randomNo]@x32'
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),                                                        
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_IPHONE)]
        resp = opener.open(url)
        #response = resp.read()
        resp.close()
        SAVE_COOKIE(cj)        

    def GET_S_VI_COOKIE(self, referer):
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        ck = cookielib.Cookie(version=0, name='s_cc', value='true', port=None, port_specified=False, domain='.comcast.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)
        ck = cookielib.Cookie(version=0, name='s_sq', value='%5B%5BB%5D%5D', port=None, port_specified=False, domain='.comcast.net', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
        cj.set_cookie(ck)

        url = "https://serviceos.comcast.net/b/ss/comcastnet/1/H.20.2/s24330211423803?AQB=1&ndh=1&t=20/5/2015%208%3A51%3A40%206%20240&ce=ISO-8859-1&ns=comcast&pageName=mobile%20app%20sign%20in&g=https%3A//login.comcast.net/login%3Fr%3Dcomcast.net%26s%3Dsso-pf%26continue%3Dhttps%253A%252F%252Fidp.comcast.net%252Fidp%252F83dOB%252FresumeSAML20%252Fidp%252FSSO.ping%253Fresponse%253D1%2526ref_url%253Dhttps%25253A%25252F%25252Fsp.auth.adobe.com%25252F%25252Fadobe-services%25252F1.0%25252Fauthenticate%252&r=https%3A//sp.auth.adobe.com//adobe-services/1.0/authenticate/saml%3Fdomain_name%3Dadobe.com%26noflash%3Dtrue%26mso_id%3DComcast_SSO%26requestor_id%3Dnbcsports%26no_iframe%3Dtrue%26client_type%3DiOS%26client_version%3D1.9%26redirect_url%3Dhttp%3A//adobepass.ios.app/&cc=USD&ch=sign%20in&events=event11&c1=/login/%3Amobile%20app%20sign%20in&v1=/login/%3Amobile%20app%20sign%20in&h1=comcast%3Acim%3Acomcast%20net%3Asign%20in%3Amobile%20app%20sign%20in&h2=/login&c4=sign%20in&c7=https%3A//saml.sp.auth.adobe.com/on-behalf-of/nbcsports&v7=https%3A//saml.sp.auth.adobe.com/on-behalf-of/nbcsports&c31=comcast&v31=mobile%20app%20sign%20in&c32=cim&v32=cim&c33=comcast%20net&v33=comcast%20net&c34=comcast%20net%3Asign%20in&c35=authentication&v35=authentication&c36=site%3Ahome&v36=site%3Ahome&c44=anonymous%3Amobile%20app%20sign%20in&v47=anonymous&s=320x568&c=32&j=1.6&v=N&k=Y&bw=320&bh=568&p=QuickTime%20Plug-in%3B&AQE=1"
        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = [ ("Accept", "*/*"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),                                                        
                            ("Connection", "keep-alive"),
                            ("Referer", referer),
                            ("User-Agent", UA_IPHONE)]
        resp = opener.open(url)        
        resp.close()
        SAVE_COOKIE(cj)
        

