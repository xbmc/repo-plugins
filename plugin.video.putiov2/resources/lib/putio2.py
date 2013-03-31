# -*- coding: utf-8 -*-
"""
A python wrapper for put.io APIv2

https://github.com/putdotio/putio-apiv2-python

Documentation: See https://api.put.io/v2/docs

Usage:

import putio2
client = putio2.Client('..oauth token here...')
# list files
files = client.File.list()
...
# add a new transfer
client.Transfer.add('http://example.com/good.torrent')

"""

import os
import re
import json
import logging
from urllib import urlencode

import requests
import iso8601

logger = logging.getLogger(__name__)

API_URL = 'https://api.put.io/v2'
ACCESS_TOKEN_URL = 'https://api.put.io/v2/oauth2/access_token'
AUTHENTICATION_URL = 'https://api.put.io/v2/oauth2/authenticate'


class AuthHelper(object):
    
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = redirect_uri
    
    def get_authentication_url(self):
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.callback_url
        }
        query_str = urlencode(query)
        return AUTHENTICATION_URL + "?" + query_str
    
    def get_access_token(self, code):
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.callback_url,
            'code': code
        }
        r = requests.get(ACCESS_TOKEN_URL, params=params, verify=False)
        d = json.loads(r.content)
        return d['access_token']


class Client(object):
    
    def __init__(self, access_token):
        self.access_token = access_token

        # Keep resource classes as attributes of client.
        # Pass client to resource classes so resource object
        # can use the client.
        attributes = {'client': self}
        self.File = type('File', (_File,), attributes)
        self.Transfer = type('Transfer', (_Transfer,), attributes)
    
    def request(self, path, method='GET', params=None, data=None, files=None, headers=None, raw=False):
        '''
Wrapper around requests.request()

Prepends API_URL to path.
Inserts oauth_token to query params.
Parses response as JSON and returns it.

'''

        if not params:
            params = {}
        params['oauth_token'] = self.access_token
        
        url = API_URL + path
        logger.debug('url: %s', url)
        r = requests.request(method, url, params=params, data=data, files=files, headers=headers, allow_redirects=True, verify=False)
        logger.debug('response: %s', r)
        
        if raw:
            return r
        
        logger.debug('content: %s', r.content)
        try:
            r = json.loads(r.content)
        except ValueError:
            raise Exception('Server didn\'t send valid JSON:\n%s\n%s' % (r, r.content))
        
        if r['status'] == 'ERROR':
            raise Exception(r['error_type'])
        
        return r


class _BaseResource(object):
    
    def __init__(self, resource_dict):
        '''Construct the object from a dict'''
        self.__dict__.update(resource_dict)
        try:
            self.created_at = iso8601.parse_date(self.created_at)
        except:
            pass
    
    def __str__(self):        
        return self.name.encode('utf-8')
        
    def __repr__(self):
        try:
            # shorten name for display
            name = self.name[:17] + '...' if len(self.name) > 20 else self.name
            return '%s(id=%s, name="%s")' % (self.__class__.__name__, self.id, str(self))
        except:
            return object.__repr__()
        

class _File(_BaseResource):
        
    @classmethod
    def list(cls, parent_id=0, as_dict=False):
        d = cls.client.request('/files/list', params={'parent_id': parent_id})
        files = d['files']
        files = [cls(f) for f in files]
        if as_dict:
            ids = [f.id for f in files]
            return dict(zip(ids, files))
        return files

    @classmethod
    def GET(cls, id=0, as_dict=False):
        d = cls.client.request('/files/%s' % id, params={})
        f = cls(dict(d['file']))
        return f

    
    @classmethod
    def upload(cls, path, name):
        f = open(path)
        files = {'file': (name, f)}
        d = cls.client.request('/files/upload', method='POST', files=files)
        f.close()
        f = d['file']
        return cls(f)

    @property
    def files(self):
        '''Helper function for listing inside of directory'''
        return self.list(parent_id=self.id)
    
    @property
    def stream_url(self):
        return API_URL + '/files/%s/stream?oauth_token=%s' % (self.id, self.client.access_token)

    def download(self, dest='.', range=None):
        if range:
            headers = {'Range': 'bytes=%s-%s' % range}
        else:
            headers = None
            
        r = self.client.request('/files/%s/download' % self.id, raw=True, headers=headers)
        
        if range:
            return r.content
            
        filename = re.match('attachment; filename\="(.*)"', r.headers['Content-Disposition']).groups()[0]
        with open(os.path.join(dest, filename), 'wb') as f:
            for data in r.iter_content():
                f.write(data)

    def delete(self):
        return self.client.request('/files/%s/delete' % self.id)


class _Transfer(_BaseResource):
        
    @classmethod
    def list(cls, parent_id=0, as_dict=False):
        d = cls.client.request('/transfers/list')
        transfers = d['transfers']
        transfers = [cls(t) for t in transfers]
        if as_dict:
            ids = [t.id for t in transfers]
            return dict(zip(ids, transfers))
        return transfers
    
    @classmethod
    def add(cls, url, parent_id=0, extract=False):
        d = cls.client.request('/transfers/add', method='POST', data=dict(
            url=url, parent_id=parent_id, extract=extract))
        t = d['transfer']
        return cls(t)