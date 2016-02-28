from urllib2 import Request, urlopen

from fivehundredpx import oauth
from fivehundredpx.settings import *
from fivehundredpx.errors 	import *

class OAuthHandler(object):
	
    def __init__(self,consumer_key,consumer_secret,callback=None,secure=True):
        self._consumer 	   = oauth.OAuthConsumer(consumer_key,consumer_secret)
        self._sigmethod    = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.request_token = None
        self.access_token  = None
        self.callback 	   = callback
        self.username 	   = None
        self.secure 	   = secure
        self.host 		   = API_HOST
        self.version 	   = API_VERSION
        self.root 		   = OAUTH_ROOT

    def _get_oauth_url(self,endpoint,secure=True):
        prefix = 'https://' if (self.secure or secure) else 'http://'
        return prefix + self.host + self.version + self.root + endpoint

    def set_request_token(self, key, secret):
        self.request_token = oauth.OAuthToken(key, secret)

    def set_access_token(self, key, secret):
        self.access_token = oauth.OAuthToken(key, secret)

    def get_request_token(self):
        url = self._get_oauth_url('request_token')
        request = oauth.OAuthRequest.from_consumer_and_token(self._consumer, http_url=url, callback=self.callback)
        request.sign_request(self._sigmethod,self._consumer,None)
        response = urlopen(Request(url,headers=request.to_header()))
        return oauth.OAuthToken.from_string(response.read())

    def apply_auth(self,url,method,headers,parameters):
        request = oauth.OAuthRequest.from_consumer_and_token(
            self._consumer,
            http_url    = url,
            http_method = method,
            token		= self.access_token,
            parameters	= parameters
        )
        request.sign_request(self._sigmethod,self._consumer,self.access_token)
        headers.update(request.to_header())
        return request

    def get_authorization_url(self):
        try:
            self.request_token = self.get_request_token()
            request = oauth.OAuthRequest.from_token_and_callback(
                token=self.request_token, http_url=self._get_oauth_url('authorize')
            )
            return request.to_url()
        except Exception, e:
            raise FiveHundredClientError(e)

    def get_access_token(self,verifier=None):
        try:
            url = self._get_oauth_url('access_token')
            request = oauth.OAuthRequest.from_consumer_and_token(
		        self._consumer, token=self.request_token, http_url=url, verifier=str(verifier)
            )
            request.sign_request(self._sigmethod, self._consumer, self.request_token)
            response = urlopen(Request(url,headers=request.to_header()))
            self.access_token = oauth.OAuthToken.from_string(response.read())
            return self.access_token
        except Exception, e:
            raise FiveHundredClientError(e)

    def get_xauth_access_token(self,username,password):
        try:
            url = self._get_oauth_url('access_token',secure=True)
            request = oauth.OAuthRequest.from_consumer_and_token(
		        oauth_consumer=self._consumer,
                token=self.request_token,
		        http_method='POST',
		        http_url=url,
		        parameters={
		            'x_auth_mode': 'client_auth',
		            'x_auth_username': username,
		            'x_auth_password': password
		        }
		    )
            request.sign_request(self._sigmethod,self._consumer,self.request_token)
            response = urlopen(Request(url,data=request.to_postdata()))
            self.access_token = oauth.OAuthToken.from_string(response.read())
            return self.access_token
        except Exception, e:
            raise FiveHundredClientError(e)	
