from resources.globals import *


class ADOBE():    

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

    def POST_ASSERTION_CONSUMER_SERVICE(self,saml_response,relay_state):
        ###################################################################
        # SAML Assertion Consumer
        ###################################################################        
        url = 'https://sp.auth.adobe.com/sp/saml/SAMLAssertionConsumer'
        
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        cookies = ''
        for cookie in cj:            
            #if (cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "client_type" or cookie.name == "client_version" or cookie.name == "JSESSIONID" or cookie.name == "redirect_url") and cookie.domain == "sp.auth.adobe.com":
            if cookie.domain == "sp.auth.adobe.com":
                cookies = cookies + cookie.name + "=" + cookie.value + "; "


        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True    
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Encoding": "gzip, deflate",
                            "Accept-Language": "en-us",
                            "Content-Type": "application/x-www-form-urlencoded",
                            #"Proxy-Connection": "keep-alive",
                            "Connection": "keep-alive",
                            "Origin": ORIGIN,
                            "Referer": REFERER,
                            "Cookie": cookies,
                            "User-Agent": UA_IPHONE}


        body = urllib.urlencode({'SAMLResponse' : saml_response,
                                 'RelayState' : relay_state
                                 })

        
        response, content = http.request(url, 'POST', headers=headers, body=body)        
        xbmc.log('POST_ASSERTION_CONSUMER_SERVICE------------------------------------------------')
        xbmc.log(str(headers))
        xbmc.log(str(body))
        xbmc.log(str(response))
        xbmc.log(str(content))
        xbmc.log('-------------------------------------------------------------------------------')
        
    

    def POST_SESSION_DEVICE(self,signed_requestor_id):
        ###################################################################
        # Create a Session for Device
        ###################################################################                
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        
        
        cookies = ''
        for cookie in cj:            
            if (cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "client_type" or cookie.name == "client_version" or cookie.name == "JSESSIONID" or cookie.name == "redirect_url") and cookie.path == "/":
                cookies = cookies + cookie.name + "=" + cookie.value + "; "
        
        
        url = 'https://sp.auth.adobe.com//adobe-services/1.0/sessionDevice'        
        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True    
        headers = { "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-us",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Proxy-Connection": "keep-alive",
                    "Connection": "keep-alive",                                                
                    "Cookie": cookies,
                    "User-Agent": UA_ADOBE_PASS}
        
        data = urllib.urlencode({'requestor_id' : 'nbcsports',
                                 '_method' : 'GET',
                                 'signed_requestor_id' : signed_requestor_id,
                                 'device_id' : DEVICE_ID
                                })
        
                
        response, content = http.request(url, 'POST', headers=headers, body=data)
        xbmc.log('POST_SESSION_DEVICE------------------------------------------------------------')
        xbmc.log(str(headers))
        xbmc.log(str(data))
        xbmc.log(str(response))
        xbmc.log(str(content))
        xbmc.log('-------------------------------------------------------------------------------')
        
        xbmc.log(content)
        auth_token = FIND(content,'<authnToken>','</authnToken>')
        xbmc.log("AUTH TOKEN")
        xbmc.log(str(auth_token))
        auth_token = auth_token.replace("&lt;", "<")
        auth_token = auth_token.replace("&gt;", ">")
        # this has to be last:
        auth_token = auth_token.replace("&amp;", "&")
        xbmc.log(auth_token)

        #Save auth token to file for         
        fname = os.path.join(ADDON_PATH_PROFILE, 'auth.token')
        #if not os.path.isfile(fname):            
        device_file = open(fname,'w')   
        device_file.write(auth_token)
        device_file.close()

        #return auth_token, session_guid        
   

    def POST_AUTHORIZE_DEVICE(self,resource_id,signed_requestor_id):
        ###################################################################
        # Authorize Device
        ###################################################################
        fname = os.path.join(ADDON_PATH_PROFILE, 'auth.token')
        device_file = open(fname,'r') 
        auth_token = device_file.readline()
        device_file.close()
        
        if auth_token == '':
            return ''

        url = 'https://sp.auth.adobe.com//adobe-services/1.0/authorizeDevice'
        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True    
        headers = {"Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-us",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Proxy-Connection": "keep-alive",
                    "Connection": "keep-alive",                                                                
                    "User-Agent": UA_ADOBE_PASS}

        data = urllib.urlencode({'requestor_id' : 'nbcsports',
                                 'resource_id' : resource_id,
                                 'signed_requestor_id' : signed_requestor_id,
                                 'mso_id' : MSO_ID,
                                 'authentication_token' : auth_token,
                                 'device_id' : DEVICE_ID,
                                 'userMeta' : '1'                             
                                })
        
        print data
        response, content = http.request(url, 'POST', headers=headers, body=data)
        
        print content        
        print response

        try:
            print "REFRESHED COOKIE"
            adobe_pass = response['set-cookie']
            print adobe_pass
            cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
            #BIGipServerAdobe_Pass_Prod=526669578.20480.0000; expires=Fri, 19-Jun-2015 19:58:42 GMT; path=/
            value = FIND(adobe_pass,'BIGipServerAdobe_Pass_Prod=',';')
            expires = FIND(adobe_pass,'expires=',' GMT;')
            #date_time = '29.08.2011 11:05:02'        
            #pattern = '%d.%m.%Y %H:%M:%S'
            #Fri, 19-Jun-2015 19:58:42
            pattern = '%a, %d-%b-%Y %H:%M:%S'
            print expires
            expires_epoch = int(time.mktime(time.strptime(expires, pattern)))
            print expires_epoch
            ck = cookielib.Cookie(version=0, name='BIGipServerAdobe_Pass_Prod', value=value, port=None, port_specified=False, domain='sp.auth.adobe.com', domain_specified=True, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=expires_epoch, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            cj.set_cookie(ck)
            #cj.save(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True);
            SAVE_COOKIE(cj)

        except:
            pass
        authz = FIND(content,'<authzToken>','</authzToken>')                
        authz = authz.replace("&lt;", "<")
        authz = authz.replace("&gt;", ">")
        # this has to be last:
        authz = authz.replace("&amp;", "&")
        print "AUTH Z TOKEN"
        print authz
        
        return authz


    def POST_SHORT_AUTHORIZED(self,signed_requestor_id,authz):
        ###################################################################
        # Short Authorize Device
        ###################################################################
        fname = os.path.join(ADDON_PATH_PROFILE, 'auth.token')
        device_file = open(fname,'r') 
        auth_token = device_file.readline()
        device_file.close()

        session_guid = FIND(auth_token,'<simpleTokenAuthenticationGuid>','</simpleTokenAuthenticationGuid>')
        print "SESSION GUID"
        print session_guid    

        url = 'https://sp.auth.adobe.com//adobe-services/1.0/deviceShortAuthorize'
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [ ("Accept", "*/*"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),                                                                            
                            ("User-Agent", UA_ADOBE_PASS)]
        

        data = urllib.urlencode({'requestor_id' : 'nbcsports',                             
                                 'signed_requestor_id' : signed_requestor_id,
                                 'mso_id' : MSO_ID,
                                 'session_guid' : session_guid,
                                 'hashed_guid' : 'false',
                                 'authz_token' : authz,
                                 'device_id' : DEVICE_ID
                                })

        resp = opener.open(url, data)
        media_token = resp.read()
        resp.close()    
        print media_token

        return media_token

    def TV_SIGN(self, media_token, resource_id, stream_url):    
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        #print cj
        cookies = ''
        for cookie in cj:        
            if cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "JSESSIONID":
                cookies = cookies + cookie.name + "=" + cookie.value + "; "

        url = 'http://sp.auth.adobe.com//tvs/v1/sign'
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [ ("Accept", "*/*"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en;q=1"),
                            ("Content-Type", "application/x-www-form-urlencoded"),                                                                                         
                            ("Cookie", cookies),
                            ("User-Agent", "NBCSports/4.2.0 (iPhone; iOS 8.3; Scale/2.00)")]
        

        data = urllib.urlencode({'cdn' : 'akamai',
                                 'mediaToken' : base64.b64encode(media_token),
                                 'resource' : base64.b64encode(resource_id),
                                 'url' : stream_url
                                })

        resp = opener.open(url, data)
        url = resp.read()
        resp.close()    
        
        return url
        