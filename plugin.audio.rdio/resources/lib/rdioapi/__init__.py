'''A Python library for accessing the Rdio web service API with OAuth

Copyright (c) 2010-2011 Rdio Inc
See individual source files for other copyrights.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''


__author__ = "Rdio <api@rd.io>"
__copyright__ = "Copyright 2010-2011, Rdio Inc. httplib2 copyright Joe Gregorio. oauth copyright Leah Culver, Joe Stump, Mark Paschal, Vic Fryzel"
__contributors__ = ['Ian McKellar']
__version__ = "1.0.0"
__license__ = "MIT"


import sys, os
import oauth2 as oauth
from cgi import parse_qsl
import urllib, logging
try:
  from django.utils import simplejson as json
except ImportError:
  import json

class RdioMethod(object):
    def __init__(self, name, rdio):
        self.name = name
        self.rdio = rdio

    def __call__(self, **args):
        return self.rdio.call(self.name, **args)

class RdioException(BaseException):
    pass

class RdioProtocolException(RdioException):
    def __init__(self, code, content):
        RdioException.__init__(self)
        self.code = code
        self.content = content
    def __str__(self):
        return 'RdioProtocolException %s: %s' % (self.code, self.content)    

class RdioAPIException(RdioException):
    def __init__(self, message):
        RdioException.__init__(self, message)


class Rdio(object):
    def __init__(self, consumer_token, consumer_secret, data_store,
                 endpoint='http://api.rdio.com/1/',
                 request_token='http://api.rdio.com/oauth/request_token',
                 access_token='http://api.rdio.com/oauth/access_token'):
        self.__consumer = oauth.Consumer(consumer_token, consumer_secret)
        self.__data_store = data_store
        self.__endpoint = endpoint
        self.__request_token = request_token
        self.__access_token = access_token

    @property
    def authenticating(self):
        '''Is the library in the middle of authenticating?'''
        return self.__data_store.has_key('request_token') and self.__data_store['request_token']

    @property
    def authenticated(self):
        '''Does the library have authentication information in the data store?'''
        return self.__data_store.has_key('access_token') and self.__data_store['access_token']


    def begin_authentication(self, callback_url):
        '''Begin authenticating process using the supplied callback URL.'''
        if self.authenticating or self.authenticated:
          self.logout()

        resp, content = self.__client().request(self.__request_token, 'POST',
                                       urllib.urlencode({'oauth_callback':callback_url}))
        if resp['status'] != '200':
            raise RdioProtocolException(resp['status'], content)
        request_token = dict(parse_qsl(content))
        self.__data_store['request_token'] = request_token
        return request_token['login_url']+'?oauth_token='+request_token['oauth_token']


    def complete_authentication(self, oauth_verifier):
        '''Complete authentication using the supplied verifier.'''
        client = self.__client(oauth_verifier)
        resp, content = client.request(self.__access_token, "POST")
        if resp['status'] != '200':
            raise RdioProtocolException(resp['status'], content)
        access_token = dict(parse_qsl(content))
        self.__data_store['access_token'] = access_token
        del self.__data_store['request_token']


    def logout(self):
        '''Clear authentication information.'''
        if self.authenticating:
            del self.__data_store['request_token']
        if self.authenticated:
            del self.__data_store['access_token']


    def __client(self, oauth_verifier=None):
        token = None
        if self.authenticated:
            at = self.__data_store['access_token']
            token = oauth.Token(at['oauth_token'], at['oauth_token_secret'])
        elif self.authenticating:
            rt = self.__data_store['request_token']
            token = oauth.Token(rt['oauth_token'], rt['oauth_token_secret'])
        if token is not None and oauth_verifier is not None:
            token.set_verifier(oauth_verifier)
        return oauth.Client(self.__consumer, token)


    def call(self, method, **args):
        '''Call a method on the Rdio service and return the result as a
        Python object. If there's an error then throw an appropriate
        exception.'''
        resp, content = self.call_raw(method, **args)
        if resp['status'] != '200':
            raise RdioProtocolException(resp['status'], content)
        response = json.loads(content)
        if response['status'] == 'ok':
            return response['result']
        else:
            raise RdioAPIException(response['message'])

        
    def call_raw(self, method, **args):
        '''Call a method on the Rdio service and return the raw HTTP result,
        a response object and the content object. See the httplib2 request
        method for examples'''
        args['method'] = method
        client = self.__client()
        return client.request(self.__endpoint, 'POST', urllib.urlencode(args))

        
    def __getattr__(self, name):
        return RdioMethod(name, self)
