import os, sys
import uuid, hmac, hashlib, base64, time
import xbmc, xbmcgui, xbmcaddon
import cookielib, urllib, urllib2, json
from urllib2 import URLError, HTTPError


class ADOBE():        
    REGGIE_FQDN = 'http://api.auth.adobe.com'
    SP_FQDN = 'http://api.auth.adobe.com'
    app_id = ''
    app_version = ''    
    device_id = ''
    device_type = ''
    devic_user = ''
    mvpd_id = ''
    private_key = ''
    public_key = ''
    reg_code = ''   
    registration_url = ''     
    requestor_id = ''
    resource_id = ''
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'


    def __init__(self, service_vars):        
        #service_vars is a dictionary type variable (key: value)        

        self.device_id = self.getDeviceID()
        
        #Mandatory Parameters
        self.requestor_id = service_vars['requestor_id']
        self.public_key = service_vars['public_key']
        self.private_key = service_vars['private_key']
        self.registration_url = service_vars['registration_url']     
        self.resource_id = service_vars['resource_id']

        #Optional Parameters
        if 'app_id' in service_vars: self.app_id = service_vars['app_id']
        if 'app_version' in service_vars: self.app_version = service_vars['app_version']        
        if 'device_type' in service_vars: self.device_type = service_vars['device_type']
        if 'device_user' in service_vars: self.device_user = service_vars['device_user']
        if 'mvpd_id' in service_vars: self.mvpd_id = service_vars['mvpd_id']
        
               

    def getDeviceID(self):
        addon_profile_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        fname = os.path.join(addon_profile_path, 'device.id')
        if not os.path.isfile(fname):
            if not os.path.exists(addon_profile_path):
                os.makedirs(addon_profile_path)         
            new_device_id =str(uuid.uuid1())
            device_file = open(fname,'w')   
            device_file.write(new_device_id)
            device_file.close()

        fname = os.path.join(addon_profile_path, 'device.id')
        device_file = open(fname,'r') 
        device_id = device_file.readline()
        device_file.close()
        
        return device_id


    def createAuthorization(self, request_method, request_uri):        
        nonce = str(uuid.uuid4())
        epochtime = str(int(time.time() * 1000))        
        authorization = request_method + " requestor_id="+self.requestor_id+", nonce="+nonce+", signature_method=HMAC-SHA1, request_time="+epochtime+", request_uri="+request_uri
        signature = hmac.new(self.private_key , authorization, hashlib.sha1)
        signature = base64.b64encode(signature.digest())
        authorization += ", public_key="+self.public_key+", signature="+signature

        return authorization



    def registerDevice(self):             
        '''
        <REGGIE_FQDN>/reggie/v1/{requestorId}/regcode    
        Returns randomly generated registration Code and login Page URI 
        '''        
        reggie_url = '/reggie/v1/'+self.requestor_id+'/regcode'
        authorization = self.createAuthorization('POST',reggie_url)       
        url = self.REGGIE_FQDN+reggie_url
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "gzip, deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]
        
                
        body = 'registrationURL=' + self.registration_url
        body += '&ttl=3600'
        body += '&deviceId='+self.device_id
        body += '&format=json'
        if self.app_id != '': body += '&appId=' + self.app_id
        if self.app_version != '': body += '&appVersion=' + self.app_version
        if self.device_type != '': body += '&deviceType=' + self.device_type
        if self.mvpd_id != '': body += '&mvpd=' + self.mvpd_id
                
        status_code, json_source = self.requestJSON(url, headers, body)       
        self.reg_code = json_source['code']

        msg = '1. Go to [B][COLOR yellow]'+self.registration_url+'[/COLOR][/B][CR]'        
        msg += '2. Select any platform, it does not matter[CR]'
        msg += '3. Enter [B][COLOR yellow]'+self.reg_code+'[/COLOR][/B] as your activation code'        
        
        dialog = xbmcgui.Dialog()         
        ok = dialog.ok('Activate Device', msg)  


    def preAuth(self):
        '''
        <SP_FQDN>/api/v1/preauthorize
        Retrieves the list of preauthorized resource
        '''
        preauth_url = '/api/v1/preauthorize'
        authorization = self.createAuthorization('GET',preauth_url)
        url = self.REGGIE_FQDN + preauth_url
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        url += '&resource='+self.resource_id
        url += '&format=json'
        #req = urllib2.Request(url)

        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)        

        

    def authorize(self):  
        '''
        <SP_FQDN>/api/v1/authorize
        Obtains authorization response

        200 - Success
        403 - No Success        
        '''      
        auth_url = '/api/v1/authorize'
        authorization = self.createAuthorization('GET',auth_url)
        url = self.REGGIE_FQDN+auth_url
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        url += '&resource='+self.resource_id 
        url += '&format=json'
        #req = urllib2.Request(url)

        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)
        #self.mvpd_id = json_source['mvpd']
        if status_code != 200:
            msg = json_source
            dialog = xbmcgui.Dialog()         
            ok = dialog.ok('Authorization Failed', msg)  
            return False
        else:
            return True
        

 
    def deauthorizeDevice(self):     
        '''
        <SP_FQDN>/api/v1/logout
        Remove AuthN and AuthZ tokens from storage 
        '''   
        auth_url = '/api/v1/logout'
        authorization = self.createAuthorization('DELETE',auth_url)
        url = self.REGGIE_FQDN+auth_url
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        url += '&format=json'
        #req = urllib2.Request(url)

        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        try: status_code, json_source = self.requestJSON(url, headers, None, 'DELETE')
        except: pass
     

    def mediaToken(self):
        '''
        <SP_FQDN>/api/v1/mediatoken
        Obtains Short Media Token 
        '''
        token_url = '/api/v1/mediatoken'
        #url = 'http://api.auth.adobe.com/api/v1/mediatoken'
        url = self.REGGIE_FQDN+token_url
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id        
        url += '&resource='+self.resource_id 
        url += '&format=json'
        authorization = self.createAuthorization('GET', token_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)

        return json_source['serializedToken']


    def getAuthN(self):
        '''                
        <SP_FQDN>/api/v1/tokens/authn 
        Returns the AuthN token if found

        200 - Success
        404 - Not Found
        410 - Expired
        '''
        authn_url = '/api/v1/tokens/authn'
        #url = 'http://api.auth.adobe.com/api/v1/tokens/authn'
        url = self.SP_FQDN+authn_url
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id        
        url += '&resource='+self.resource_id 
        url += '&format=json'
        authorization = self.createAuthorization('GET', authn_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)

        auth_info = ''
        try:
            auth_info = 'Provider: ' + json_source['mvpd'] + ' expires on ' + json_source['expires']
        except:
            pass

        return auth_info

    def checkAuthN(self):
        '''
        <SP_FQDN>/api/v1/checkauthn
        Indicates whether the device has an unexpired AuthN token. 

        200 - Success 
        403 - No Success
        '''
        authn_url = '/api/v1/checkauthn'
        url = self.SP_FQDN+authn_url        
        url += '?deviceId='+self.device_id
        url += '&format=json'
        authorization = self.createAuthorization('GET', authn_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)

        if status_code == 200:
            return True
        else:
            return False



    def getAuthZ(self):
        '''
        <SP_FQDN>/api/v1/tokens/authz
        Returns the AuthZ token if found

        200 - Success
        412 - No AuthN
        404 - No AuthZ
        410 - AuthZ Expired
        '''
        authn_url = '/api/v1/tokens/authz'
        url = self.SP_FQDN+authn_url   
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        url += '&resource='+self.resource_id 
        url += '&format=json'
        authorization = self.createAuthorization('GET', authn_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)


    def userMetaData(self):
        '''
        <SP_FQDN>/api/v1/tokens/usermetadata    
        Gets user metadata after authentication flow completes

        200 - Success
        404 - No metadata found
        412 - Invalid AuthN Token
                 (e.g., expired token)
        '''
        authn_url = '/api/v1/tokens/authz'
        url = self.SP_FQDN+authn_url   
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        #url += '&appId='+urllib.quote(resource_id)
        url += '&format=json'
        authorization = self.createAuthorization('GET', authn_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)


    def tempPass(self):
        '''
        <SP_FQDN>/api/v1/authenticate/freepreview   
        Create an authentication token for Temp Pass or Promotional Temp Pass

        204 - No Content 
        400 - Bad request
        * The successful response will be a 204 No Content, indicating that the token was successfully created and is ready to use for the authz flows.
        '''

        preview_url = '/api/v1/authenticate/freepreview'
        url = self.SP_FQDN+authn_url   
        url += '?deviceId='+self.device_id
        url += '&requestor='+self.requestor_id
        #url += '&appId='+urllib.quote(resource_id)
        url += '&format=json'
        authorization = self.createAuthorization('GET', authn_url)
        headers = [ ("Accept", "*/*"),
                    ("Content-type", "application/x-www-form-urlencoded"),
                    ("Authorization", authorization),
                    ("Accept-Language", "en-US"),
                    ("Accept-Encoding", "deflate"),
                    ("User-Agent", self.user_agent),
                    ("Connection", "Keep-Alive"),                    
                    ("Pragma", "no-cache")
                    ]

        status_code, json_source = self.requestJSON(url, headers)


    def requestJSON(self, url, headers, body=None, method=None):      
        addon_profile_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))  
        cj = cookielib.LWPCookieJar(os.path.join(addon_profile_path, 'cookies.lwp'))
        try: cj.load(os.path.join(addon_profile_path, 'cookies.lwp'),ignore_discard=True)
        except: pass
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))    
        opener.addheaders = headers     
        json_source = ''        
        status_code = 0
        try:           
            request = urllib2.Request(url, body)
            if method == 'DELETE': request.get_method = lambda: method            
            response = opener.open(request)
            status_code = response.getcode()
            json_source = json.load(response) 
            response.close()
            self.saveCookie(cj)
        except HTTPError as e:
            status_code = e.code
            json_source = e.read()    
        except:
            pass        
            

        return status_code, json_source


    def saveCookie(self, cj):
        # Cookielib patch for Year 2038 problem
        # Possibly wrap this in if to check if device is using a 32bit OS
        for cookie in cj:
            # Jan, 1 2038
            if cookie.expires >= 2145916800:
                #Jan, 1 2037
                cookie.expires =  2114380800
        
        cj.save(ignore_discard=True)  