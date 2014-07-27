# -*- coding: utf-8 -*-
"""
A python wrapper for Cessfull APIv1

"""

import os
import re
import json
import logging
from urllib import urlencode

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

API_URL = 'https://www.cessfull.com/api/v1'
AUTHENTICATION_URL = 'https://www.cessfull.com/api/v1/connect/token/'


class AuthHelper(object):
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def get_authentication_url(self):
        r = requests.get(AUTHENTICATION_URL, auth=HTTPBasicAuth(self.username, self.password))
        if r.status_code == 200:
            d = json.loads(r.content)
            return d['key']
        else:
            return False


class Client(object):
    
    def __init__(self, username, api_key):
        self.api_key = api_key
        self.username = username

        # Keep resource classes as attributes of client.
        # Pass client to resource classes so resource object
        # can use the client.
        attributes = {'client': self}
        self.File = type('File', (_File,), attributes)
    
    def request(self, path, method='GET', params=None, data=None, files=None, headers=None, raw=False):
        '''
            Wrapper around requests.request()

            Prepends API_URL to path.
            Inserts username and api_key to query params.
            Parses response as JSON and returns it.

        '''

        if not params:
            params = {}
        params['api_key'] = self.api_key
        params['username'] = self.username
        
        url = API_URL + path
        logger.debug('url: %s', url)
        r = requests.request(method, url, params=params, data=data, files=files, headers=headers, allow_redirects=True)
        logger.debug('response: %s', r)
        
        if raw:
            return r
        
        logger.debug('content: %s', r.content)
        if not r.status_code == 200:
            raise Exception("Error")
        try:
            r = json.loads(r.content)
        except ValueError:
            raise Exception('Server didn\'t send valid JSON:\n%s\n%s' % (r, r.content))      
        
        
        return r


class _BaseResource(object):
    
    def __init__(self, resource_dict):
        '''Construct the object from a dict'''
        self.__dict__.update(resource_dict)        
    
    def __str__(self):     
        try:
            return self.name.encode('utf-8')
        except:
            pass   
        
        
    def __repr__(self):
        try:
            # shorten name for display
            name = self.name[:17] + '...' if len(self.name) > 20 else self.name
            return '%s(id=%s, name="%s")' % (self.__class__.__name__, self.id, str(self))
        except:
            return object.__repr__()
        

class _File(_BaseResource):
        
    @classmethod
    def list(cls, id_parent=0, as_dict=False):
        d = cls.client.request('/files/', params={'id_parent': id_parent})
        files = d['items']
        files = [cls(f) for f in files]
        if as_dict:
            ids = [f.id for f in files]
            return dict(zip(ids, files))
        return files

    @classmethod
    def GET(cls, id=0, as_dict=False):
        d = cls.client.request('/files/%s' % id, params={})
        f = cls(d)
        return f