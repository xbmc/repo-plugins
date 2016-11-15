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
        last_url = resp.geturl()   
        resp.close()   
        
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
                            ("Accept-Encoding", "deflate"),
                            ("Accept-Language", "en-us"),                            
                            ("Connection", "keep-alive"),
                            ("Origin", "https://login.comcast.net"),
                            ("Referer", referer),
                            ("User-Agent", UA_IPHONE)]

        
        login_data = urllib.urlencode({'user' : USERNAME,
                                       'passwd' : PASSWORD,
                                       'reqId' : req_id,                                       
                                       'ipAddrAuthn':'true',
                                       'deviceAuthn':'false',
                                       's':'oauth',
                                       'forceAuthn':'0',
                                       'r':'comcast.net',
                                       'continue':continue_url,
                                       'passive':'false',
                                       'client_id':'adobepass-nbcsports',
                                       'lang' : 'en'
                                       })

        saml_response = "skip"
        relay_state = "skip"
        try:
            resp = opener.open(url, login_data)
            print resp.getcode()
            print resp.info()        
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
            pass
        
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
        
        url = "https://serviceos.comcast.net/b/ss/comcastnet/1/H.27.5/s41303345554477?AQB=1&pccr=true&vidn=2C0299A205011584-60000137E007532F&&ndh=1&t=17%2F9%2F2016%2016%3A23%3A32%201%20240&fid=1F8FC523BD7D4396-2E7FF98D1A765CCC&ce=UTF-8&ns=comcast&pageName=mobile%20app%20sign%20in&g=https%3A%2F%2Flogin.comcast.net%2Flogin%3Fr%3Dcomcast.net%26s%3Doauth%26continue%3Dhttps%253A%252F%252Flogin.comcast.net%252Foauth%252Fauthorize%253Fresponse_type%253Dcode%2526redirect_uri%253Dhttps%253A%252F%252Fsp.auth.adobe.com%252Fadobe-services%252Foauth2%2526state%253DQyqYoV%2526scope%253Dopenid%252520prof&cc=USD&ch=sign%20in&events=event11&c1=%2Flogin%2F%3Amobile%20app%20sign%20in&v1=%2Flogin%2F%3Amobile%20app%20sign%20in&c4=sign%20in&c7=adobepass-nbcsports&v7=adobepass-nbcsports&c23=small&c31=comcast&v31=mobile%20app%20sign%20in&c32=cim&v32=cim&c33=comcast%20net&v33=comcast%20net&c34=comcast%20net%3Asign%20in&c35=authentication&v35=authentication&c36=site%3Ahome&v36=site%3Ahome&v41=small&c44=anonymous%3Amobile%20app%20sign%20in&v47=anonymous&h1=comcast%3Acim%3Acomcast%20net%3Asign%20in%3Amobile%20app%20sign%20in&h2=%2Flogin&s=375x667&c=32&j=1.6&v=N&k=Y&bw=375&bh=667&-g=ile%252520https%253A%252F%252Flogin.comcast.net%252Fpdp%252Ftve%2526client_id%253Dadobepass-nbcsports%2526acr_values%253Durn%253Aoasis%253Anames%253Atc%253ASAML%253A2.0%253Aac%253Aclasses%253AInternetProtocol%2526response%253D1%26reqId%3D51e0dfcb-71e4-4a3f-96ad-8b8366155e6b%26ipAddrAuthn%3D1%26client_id%3Dadobepass-nbcsports&AQE=1"
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
        

