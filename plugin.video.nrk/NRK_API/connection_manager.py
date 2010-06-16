#connectionManager.py
#
# NRK plugin for XBMC Media center
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#


# TODO: Cleanup imports
from utils import PluginError, PluginIOError, PluginConnectionError, Key, Log, Plugin  
from urllib import urlencode, splithost, quote, unquote, quote_plus, unquote_plus
from urllib2 import urlopen, Request, URLError
from urlparse import urlparse
from threading import Thread
from time import time
import urlparse
import httplib
import urllib
import utils
import sys
import os
import re



Log.out( "PLUGIN::LOADED -> '%s'" % __name__)


if (Plugin.get_platform() == utils.WINDOWS or 
    Plugin.get_platform() == utils.XBOX):
    Log.out('PLUGIN::IMPORT -> "cPickle" module')
    import cPickle as pickle
else: 
    Log.out('PLUGIN::IMPORT -> "pickle" module')
    import pickle  
    

NONE = 0; READ = 1; WRITE = 2; BINARY = 'b'; ASCII = ''



def file_exist(file):
    if os.path.isfile(file): return True
        
        
def random_filename(pfx='',ext=''):
    import string; import random
    s = ''.join(( pfx, '_' )); e = ''.join(( '.', ext ))
    return "".join((s, random.sample(string.letters + string.digits, 8), e))
    
     
def write_to_disk(fp, file, mode='w'):

    print 'DISKWRITE:: write: path %s' % fp
    try:
        file_handle = open(fp, mode)
        file_handle.write(file)
        file_handle.close()
    except:
        raise PluginIOError(
                'Error writing to disk',
                'Plugin could not write data to cache on disk'
            )
    else: return filepath

    
def open_from_disk(fp, mode='r'):
    try:
        fh = open(fp, mode)
        data = fh.read()
        fh.close()
    except:
        raise PluginIOError(
                'Error reading file',
                'Plugin could not read data from cache on disk'
            )
    else: return data
    

    
class Cache:
    
    @staticmethod
    def has_cache(path, cache_time=None, timeformat='m'):
        if not os.path.isfile(path):
            print 'CACHE:: No file found'
            return
        
        if not cache_time:
            return True
               
        cache_time = int(cache_time)
        if timeformat == 'm': time_exp = (24* cache_time * 60)
        else: time_exp = (cache_time * 60)   
        try: mtime = os.path.getmtime(path)
        except:
            print 'CACHE:: Could not get mtime', path
            mtime = 0  
        if ((time() - time_exp) >= mtime): return
        else: return True

    
    def __init__(self, path, time, md=ASCII):
        self.path = path
        self.time = time
        self.md = md
        
        
    def write(self, fname, data, md=None):
        if not md: md = self.md
        fp = os.path.join(self.path, fname)
        write_to_disk(fp, data, 'w'+md)

   
    def open(self, fname, md=None):
        if not md: md = self.md
        fp = os.path.join(self.path, fname)
        fh = open_from_disk(fp, 'r'+md)
       
            
            

        
class DataHandle(Plugin):

    default_encoding = 'utf-8'
    
    
    def __init__(self, cache=None, httptimeout=10):
        self.cache = cache
        self.httptimeout = httptimeout
    # - EOM -
    
    
    def get_header(self, url, header):
    
        headers = self.open_connection(url, "HEAD", silent=True)
        if not headers: 
            return
            
        for head in headers:
            if head[0] == header:
                return head[1]
    # - EOM -
    
     
    def open_connection(self, url, method='GET', data='', headers={}, silent=None):
        
        # TODO: 
        # This is a mean fucker that's needs to be rewritten in
        # probably should override the httpconnection class, and make
        # some solution for setting timeout


        url = urlparse.urlparse(url); path = url[2]
        query = url[4]; hostname = url[1]

        Log.out('PLUGIN::CONNECTION -> Connection to %s requested...' % hostname)
        conn = httplib.HTTPConnection(hostname)

        # Inner function for the connection thread
        def thread_procedure(conn, path, query, data, headers, method, result):
        
            path = urllib.quote(urllib.unquote(path.encode('utf-8')), safe='/;')
            
            if method == 'GET':
                if not path:
                    path = '/'  # eg: 'http://google.com' -> 'http://google.com/'
                
                query = urllib.quote(urllib.unquote(query.encode('utf-8')), safe='=&?/')
                requestline = '%s?%s' % (path, query)
            else: 
                requestline = path

            try:
                conn.putrequest(method, requestline)
                conn.putheader('Content-length', str(len(data)))
                for key in headers: conn.putheader(key, headers[key])
                conn.endheaders()
                conn.send(data)
            except: 
              result.append(-2)
                
            else:
                response = conn.getresponse()
                print 'PLUGIN::CONNECTION -> %s -> status code: %d' % (
                                                repr(requestline), response.status)
                
                if response.status not in range(200,300):
                    result.append(-1)
                    result.append(response.status)
                    return
                
                if method == "HEAD": 
                    result.append(response.getheaders())
                else:
                    result.append( response.read() )
                    
                conn.close()
        # - EOFN - 	
            
            
        result = list()
        thread = Thread(
                target = thread_procedure,
                args = (conn, path, query, data, headers, method, result)
            )	
        thread.setDaemon(True); thread.start()
        
        if method == 'HEAD' or silent is not None:
            timeout = int(self.httptimeout / 2)
        else: timeout = self.httptimeout
            
        thread.join(timeout)
        

        if [] == result:
            if not silent:
                raise PluginConnectionError(
                        'Connection Timeout',
                        'Connection to host %s timed out' % hostname,'',
                        'No data received. Aborting...',
                    )
        elif -1 == result[0]:
            if not silent:
                raise utils.PluginHTTPError(url, result[1])
        elif -2 == result[0]:
            if not silent:
                raise PluginConnectionError(
                        'Connection Exception Direction!',
                        'Connection to host %s raised exception' % hostname,
                        'No data received. Aborting...',
                    )
        else: 
            if result[0]:
                return result[0]
            else:
                if not silent:
                    raise PluginConnectionError(
                            'No data resolved!',
                            'Connection to host %s raised exception' % hostname,
                            'No data received. Aborting...',
                        )
      
      

    def get_data( self, url, mode='GET', body='', headers={}, persistent=None, 
                  silent=None, cache=None
                ):
        
        if cache == None: cache = self.cache
        if mode == 'POST':
            key = str(hash(body))
        else:
            key = url
            
        #Check for cache if cache enabled both local and within call
        if cache == self.cache == True:
            data = Session()._checkout_session_jar(key)
            if data:
                return data
                
        # try'n cry     
        #If there where no cache or cache disabled or expired
        data = self.open_connection(url, mode, body, headers, silent)
        if data is None:
            return
        else:
            if data:
                if cache == self.cache == True:
                    Session().put_in_session_jar(key, 
                            data, persistent)

                return data
    # - EOM -
    

    
    

 

 
class ImageArchiver(DataHandle):
    
    PERSISTENT       = 1.1
    httptimeout      = 10
    default_encoding = 'utf-8'
    
    
    
    def __init__(self, cache=False):
        self.cache = cache
        self.image_archive_key = None
        self.image_archive_is_changed = False
    # - EOC -

    
    def open_image_archive(self, key):
    
        self.image_archive_key = key
        self.image_archive_is_changed = False
        
        Log.out('PLUGIN::IMAGEARCHIVER -> open with key: "%s"' % key)
        
        data = Session()._checkout_session_jar(key)
        
        if data:
            Log.out('PLUGIN::IMAGEARCHIVER ->: cache found')
            self.image_archive = data
        else: 
            Log.out('PLUGIN::IMAGEARCHIVER -> Create new archive')
            self.image_archive = {}
    # - EOM -
    
         
    def save_image_archive(self):
    
        if not self.image_archive_key:
            return
        Log.out('PLUGIN::IMAGEARCHIVER -> save with key: "%s"' % self.image_archive_key)

        if self.cache is True and self.image_archive_is_changed is True:
            Session().put_in_session_jar(
                    self.image_archive_key,
                    self.image_archive,
                    persistent = True
                )
    # - EOM -
    
    
    def archive_image(self, parent, image, id):
        
        # Silly little tuple makes life easy
        images = ('.png', '.jpg', '.gif', 'tiff')
        
        # If the thumbnail url have no length, theres little to do,
        # and if it has a known extension theres nothing to do, so return
        if len(image) < 1 or image[-4:] in images:
            return None
        
        key = 'imga_%s_%s_%s_' % (
                      str(parent.type), 
                      str(parent.view), 
                      str(parent.id) 
              )
               
        if key != self.image_archive_key:
            # If the key passed don't matches the open key
            if self.image_archive_is_changed is True:
                # and previouse archive is changed. Do save
                self.save_image_archive()
            # Open a new image archive
            self.open_image_archive(key)

        try:
            image_type = self.image_archive[id]
            
        except KeyError:
            image_type = self._get_image_type(image)
            
            if image_type is not None:
                if image_type == 'jpeg':
                    image_type = 'jpg'
                    
                self.image_archive[id] = image_type
                self.image_archive_is_changed = True
                
                print 'PLUGIN::IMAGEARCHIVER -> image url corrected'
                return image_type
                
        else:
            return image_type
    # - EOM -

    
            
    def _get_image_type(self, url):
        """Get mime type from header to determine file extension"""
        
        header = self.get_header(url, 'content-type')
        if header and header.startswith('image'):
            return header.split('/')[1]
        else:
            return
    # - EOM -
    
    
    
    
    
PERSISTENT = 1.1    



class SessionManager(Plugin):
    
    cache_never_expire = 999
    changed            = False   
    data_objects       = {}
    
    def __init__(self, val):
        try: 
            self.cache = val['cache']
        except KeyError: 
            self.cache = False
        else:
            try: 
                self.cache_time = val['cache-time']
            except: 
                self.cache = False
            else:
                try: 
                    self.cache_path = val['cache-path']
                except: 
                    self.cache = False
                else:
                    if not os.path.isdir( os.path.dirname(self.cache_path) ):
                        print 'PLUGIN::SESSION -> Create plugin cache directory'
                        os.makedirs( os.path.dirname(self.cache_path) )       
                    
        if self.cache_time is self.cache_never_expire: 
            self.never_expires = True
        else: 
            self.never_expires = None
        
        try:
            key = val['key']
        except:
            if type(val) == type(''): 
                key = val
            else: 
                key = None
        
        if key is not None: 
            self.open_session(key)
            
            
    def open(self, key):
        self.open_session(key)
    # - EOM -    
    
    
    def close(self):
        print 'PLUGIN::SESSION -> close()'
        self.save_session()
    # - EOM -
    
    
    def get_path(self, file):
        path = self.cache_path
        filename = os.path.join(path, file)
        return filename
    # - EOM -
    
    
    def manage(self, **kwargs):
        for kw in kwargs:
            obj = self._checkout_session_jar(kw)
            if not obj: obj = kwargs[kw]
            self.data_objects[kw] = obj
    # - EOM -
    
    
    def update_object(self, kw):
        self.put_in_session_jar(kw, self.data_objects[kw], True)
        return self.data_objects[kw]
    # - EOM -

    
    def _checkout_session_jar(self, key):
        
        try: exp_time = self.session_jar[key][0]
        except:
            print 'SESSION: -> data not found in jar'
            return
            
        if exp_time != PERSISTENT:
            print 'PLUGIN::SESSION -> Jar entry stamped: "%s"' % str(exp_time)
            if ((time() - (self.cache_time * 3600)) >= exp_time): 
                return
                
        try: data = self.session_jar[key][1]
        except: print 'PLUGIN::SESSION -> could not read data from jar'
        else:
            print 'PLUGIN::SESSION -> found and returning data'
            return data
    # - EOM -           
                
     
     
    def put_in_session_jar(self, key, data, persistent=None):
        
        if persistent: exp_time = PERSISTENT
        else: exp_time = time()
            
        self.session_jar[key] = ( exp_time, data )
        self.changed = True
    # - EOM -   
        
           
    def open_session(self, key):
        Log.out('PLUGIN::SESSION -> open', key=key)
        self.session_jar = self._open_session_from_disk(key)
    # - EOM -
    
      
    def swap_session(self, newkey):
        Log.out('PLUGIN::SESSION -> swap session to "%s"' % newkey)
        self.save_session()
        self.open(newkey)
    # - EOM -
    
    
    def save_session(self):
        print 'PLUGIN::SESSION -> cache: %s, changed: %s' % (
                    str(self.cache), str(self.changed))
        if self.cache is True and self.changed == True:
            self._write_session_to_disk(self.session_jar, self.session_key)
    # - EOM -
    
    
        
    def _open_session_from_disk(self, key):
    
        filepath = self.get_path(key)
        
        if not os.path.isfile(filepath):
            Log.out('PLUGIN::SESSION -> no saved data. new empty session created')
            return {}
            
        try:
            file_handle = open(filepath, 'rb')
            data = pickle.load(file_handle)
            file_handle.close()
            
        except pickle.UnpicklingError:
            print 'PLUGIN::SESSION -> An error occured unpickling saved object'
            return {}
        else:
            print 'PLUGIN::SESSION -> data with key "%s" read from disk' % key
            return data
    # - EOM -

    
            
    def _write_session_to_disk(self, data, key):

        filepath = self.get_path(key)
        print 'PLUGIN::SESSION -> save data with key "%s" to path "%s"' % (key, filepath)
        
        if os.path.isdir(os.path.dirname(filepath)) == False:
            print 'PLUGIN::SESSION -> Create directory'
            os.makedirs(os.path.dirname(filepath))  
            
        try:
            file_handle = open(filepath, 'wb')
            pickle.dump(data, file_handle)
            file_handle.close()
            
        except pickle.PicklingError:
            print 'PLUGIN::SESSION -> An error occured during pickle dump'
            
        except: 
            raise
        else: 
            self.changed = False
    # - EOM -       
    
   



class KeySession(SessionManager):
   
    def open_session(self, key):
        
        # If a new session is requested opened several times
        # it probably use of transparency or a error, so 
        # just continue to use the same variable and key 
        try: 
            self.session_jar
        except:
            # Don't have a session, so go on.. 
            pass
        else: 
            # Session allready initiated, just return..
            return
        
        if type(key) == type(''): 
            self.session_key = key
        else:
            try: 
                self.session_key = str( hash( key )  )
            except: 
                raise Exception
        
        Log.out('PLUGIN::SESSION -> try key: %s' % self.session_key)
        self.session_jar = self._open_session_from_disk(self.session_key)
        
        return self.session_key
    # - EOM -     
   
   
 
class Session:
    
    class __session_impl(KeySession):
        pass

    __inst = None

    def __init__(self, val=None):
        if Session.__inst is None:
            Session.__inst = Session.__session_impl(val)
        self.__dict__['_Session__inst'] = Session.__inst
   
    def __getattr__(self, attr):
        return getattr(self.__inst, attr)

        
    def __setattr__(self, attr, value):
        return setattr(self.__inst, attr, value)