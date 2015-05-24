#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmc
import xbmcgui
import xbmcvfs
import shutil

import os
import time
import threading, Queue

from utils import *

from dropbox import client, rest
from StringIO import StringIO

from dropboxprogress import DropboxBackgroundProgress

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

def command():
    """a decorator for handling authentication and exceptions"""
    def decorate(f):
        def wrapper(self, *args, **keywords):
            try:
                return f(self, *args, **keywords)
            except TypeError, e:
                log_error('TypeError: %s' %str(e))
            except rest.ErrorResponse, e:
                self.DropboxAPI = None
                msg = e.user_error_msg or str(e)
                log_error("%s failed: %s"%(f.__name__, msg) )
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30206), '%s' % (msg))

        wrapper.__doc__ = f.__doc__
        return wrapper
    return decorate

def path_to(path):
    '''
    Dropbox API uses "utf-8" coding!
    This functions makes sure that it is utf-8.
    '''
    if isinstance (path, unicode):
        path = path.encode("utf-8")
    return path

def path_from(path):
    '''
    Dropbox API uses "utf-8" coding, but the dropbox-API returns unicode!
    This functions makes sure that it is unicode.
    '''
    if isinstance (path, str):
        log_error("Dropbox path is not unicode! %s"%(path))
        path = path.decode("utf-8")
    return path

def getLocalSyncPath(localSyncPath, remoteSyncPath, itemPath):
    itemPath = itemPath.replace(remoteSyncPath, u'', 1)
    localPath = os.path.normpath(localSyncPath + DROPBOX_SEP + itemPath)
    return localPath


class XBMCDropBoxClient(object):
    '''
    Provides a more 'general' interface to dropbox.
    Handles all dropbox API specifics
    '''
    DropboxAPI = None
    _cache = None
    
#TODO: fix singleton --> it doesn't work!
#     _instance = None
#     def __new__(cls, *args, **kwargs):
#         if not cls._instance:
#             cls._instance = super(XBMCDropBoxClient, cls).__new__(
#                                 cls, *args, **kwargs)
#         return cls._instance

    def __init__( self, autoConnect = True , access_token = None):
        self._access_token = access_token
        #get storage server
        self._cache = StorageServer.StorageServer(ADDON_NAME, 168) # (Your plugin name, Cache time in hours)
        if autoConnect:
            succes, msg = self.connect()
            if not succes:
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30205), '%s' % (msg))

    def connect(self):
        msg = 'No error'
        #get Settings
        if not self._access_token:
            msg = 'No token (access code)'
        #get Dropbox API (handle)
        if self.DropboxAPI == None and self._access_token:
            #log_debug("Getting dropbox client with token: %s"%self._access_token)
            try:
                self.DropboxAPI = client.DropboxClient(self._access_token)
            except rest.ErrorResponse, e:
                msg = e.user_error_msg or str(e)
                self.DropboxAPI = None
        return (self.DropboxAPI != None), msg

    def disconnect(self):
        self.DropboxAPI == None

    def getFolderContents(self, path):
        contents = []
        resp, changed = self.getMetaData(path, directory=True)
        if 'contents' in resp:
            contents = resp['contents']
        return contents

    def getMetaData(self, path, directory=False):
        '''
        The metadata of the directory is cached.
        The metadata of a file is retrieved from the directory metadata.
        For caching the metadata, the StorageServer 
        (script.common.plugin.cache addon) is used.
        '''
        hashstr = None
        changed = False
        dirname = path
        if not directory:
            #strip the filename
            dirname = os.path.dirname(path)
        #Make the cache_name unique to the account (using the access_token).
        # To prevents that different accounts, which have the same directories, don't
        # use the same cache 
        cache_name = self._access_token + dirname
        #check if a hash is available
        stored = self._cache.get(cache_name)
        if stored != '':
            stored = eval(stored)
            if 'hash' in stored:
                hashstr = stored['hash']
                #log("Metadata using stored hash: %s"%hashstr)
        resp = None
        if self.DropboxAPI != None:
            if directory or stored == '':
                try:
                    resp = self.DropboxAPI.metadata(path=path_to(dirname), hash=hashstr)
                except rest.ErrorResponse, e:
                    msg = e.user_error_msg or str(e)
                    if '304' in msg:
                        #cached data is still the same
                        log_debug("Metadata using stored data for %s"%dirname)
                        resp = stored
                    else:
                        log_error("Failed retrieving Metadata: %s"%msg)
                        self.DropboxAPI = None
                        msg = e.user_error_msg or str(e)
                        dialog = xbmcgui.Dialog()
                        dialog.ok(ADDON_NAME, LANGUAGE_STRING(30206), '%s' % (msg))
                else:
                    #When no exception: store new retrieved data
                    log_debug("New/updated Metadata is stored for %s"%dirname)
                    self._cache.set(cache_name, repr(resp))
                    changed = True
            else:
                #get the file metadata using the stored data
                resp = stored
            if resp and not directory:
                #get the file metadata
                items = resp['contents']
                resp = None
                for item in items:
                    if path_from(item['path']).lower() == path.lower():
                        resp = item
                        break;
        return resp, changed

    @command()
    def getMediaUrl(self, path, cachedonly=False):
        '''
        Cache this URL because it takes a lot of time requesting it...
        If the mediaUrl is still valid, within the margin, then don't
        request a new one yet.
        '''
        margin = 20*60 #20 mins
        resp = None
        #check if stored link is still valid
        stored = self._cache.get(u"mediaUrl:"+path)
        if stored != '':
            stored = eval(stored)
            if 'expires' in stored:
                # format: "Fri, 16 Sep 2011 01:01:25 +0000"
                until = time.strptime(stored['expires'], "%a, %d %b %Y %H:%M:%S +0000")
                #convert to floats
                until = time.mktime(until)
                currentTime = time.time() 
                if(until > (currentTime + margin) ):
                    #use stored link
                    resp = stored
                    log_debug("MediaUrl using stored url.")
                else:
                    log_debug("MediaUrl expired. End time was: %s"%stored['expires'])
        if not cachedonly and resp == None and self.DropboxAPI != None:
            resp = self.DropboxAPI.media( path_to(path) )
            #store the link
            log_debug("MediaUrl storing url.")
            self._cache.set(u"mediaUrl:"+path, repr(resp))
        if resp:
            return resp['url']
        else:
            return '' 
    
    @command()
    def search(self, searchText, path):
        searchResult = self.DropboxAPI.search( path_to(path), searchText)
        return searchResult
    
    @command()
    def delete(self, path):
        succes = False
        resp = self.DropboxAPI.file_delete( path_to(path) )
        if resp and 'is_deleted' in resp:
            succes = resp['is_deleted']
        return succes

    @command()
    def copy(self, path, toPath):
        succes = False
        resp = self.DropboxAPI.file_copy(path_to(path), path_to(toPath))
        if resp and 'path' in resp:
            succes = ( path_from(resp['path']).lower() == toPath.lower())
        return succes

    @command()
    def move(self, path, toPath):
        succes = False
        resp = self.DropboxAPI.file_move(path_to(path), path_to(toPath))
        if resp and 'path' in resp:
            succes = ( path_from(resp['path']).lower() == toPath.lower())
        return succes

    @command()
    def createFolder(self, path):
        succes = False
        resp = self.DropboxAPI.file_create_folder( path_to(path) )
        if resp and 'path' in resp:
            succes = ( path_from(resp['path']).lower() == path.lower())
        return succes

    @command()
    def upload(self, fileName, toPath, dialog=False):
        succes = False
        size = os.stat(fileName).st_size
        if size > 0:
            uploadFile = open(fileName, 'rb')
            uploader = Uploader(self.DropboxAPI, uploadFile, size)
            dialog = xbmcgui.DialogProgress()
            dialog.create(LANGUAGE_STRING(30033), fileName)
            dialog.update( (uploader.offset*100) / uploader.target_length )
            while uploader.offset < uploader.target_length:
                if dialog.iscanceled():
                    log('User canceled the upload!')
                    break
                uploader.uploadNext()
                dialog.update( (uploader.offset*100) / uploader.target_length )
            dialog.close()
            if uploader.offset == uploader.target_length:
                #user didn't cancel
                path = toPath + DROPBOX_SEP + os.path.basename(fileName) 
                resp = uploader.finish(path)
                if resp and 'path' in resp:
                    succes = ( path_from(resp['path']).lower() == path.lower())
        else:
            log_error('File size of Upload file <= 0!')
        return succes
        
    def saveThumbnail(self, path, location):
        succes = False
        dirName = os.path.dirname(location) + os.sep #add os seperator because it is a dir
        # create the data dir if needed
        if not xbmcvfs.exists( dirName.encode("utf-8") ):
            xbmcvfs.mkdirs( dirName.encode("utf-8") )
        try:
            cacheFile = open(location, 'wb') # 'b' option required for windows!
            #download the file
            #jpeg (default) or png. For images that are photos, jpeg should be preferred, while png is better for screenshots and digital art.
            tumbFile = self.DropboxAPI.thumbnail( path_to(path), size='large', format='JPEG')
            shutil.copyfileobj(tumbFile, cacheFile)
            cacheFile.close()
            log_debug("Downloaded file to: %s"%location)
            succes = True
        except IOError, e:
            msg = str(e)
            log_error('Failed saving file %s. Error: %s' %(location,msg) )
        except rest.ErrorResponse, e:
            msg = e.user_error_msg or str(e)
            log_error('Failed downloading file %s. Error: %s' %(location,msg))
        return succes

    def saveFile(self, path, location):
        succes = False
        dirName = os.path.dirname(location) + os.sep #add os seperator because it is a dir 
        # create the data dir if needed
        if not xbmcvfs.exists( dirName.encode("utf-8") ):
            xbmcvfs.mkdirs( dirName.encode("utf-8") )
        try:
            cacheFile = open(location, 'wb') # 'b' option required for windows!
            #download the file
            orgFile = self.DropboxAPI.get_file( path_to(path) )
            shutil.copyfileobj(orgFile, cacheFile)
            cacheFile.close()
            log_debug("Downloaded file to: %s"%location)
            succes = True
        except IOError, e:
            msg = str(e)
            log_error('Failed saving file %s. Error: %s' %(location,msg) )
        except rest.ErrorResponse, e:
            msg = e.user_error_msg or str(e)
            log_error('Failed downloading file %s. Error: %s' %(location,msg))
        return succes

    @command()
    def getRemoteChanges(self, cursor):
        if cursor == '':
            cursor = None
        response = self.DropboxAPI.delta(cursor)
        data = response['entries']
        items = {}
        for item in data:
            meta = item[1]
            path = path_from(item[0]) #case-insensitive!
            # But cannot use the meta['path'] because it is not 
            # there when the item is removed!
            #path = path_from( meta['path'] )
            items[path] = meta
        cursor = response['cursor']
        reset = response['reset']
        has_more = response['has_more']
        return items, cursor, reset, has_more

    def getAccountInfo(self):
        resp = self.DropboxAPI.account_info()
        return resp


class Uploader(client.DropboxClient.ChunkedUploader):
    """
    Use the client.DropboxClient.ChunkedUploader, but create a
    step() function to  
    """
    def __init__( self, client, file_obj, length):
        super(Uploader, self).__init__(client, file_obj, length)
        self.chunk_size = 1*1024*1024 # 1 MB sizes

    def uploadNext(self):
        """Uploads data from this ChunkedUploader's file_obj in chunks.
        When this function is called 1 chunk is uploaded.
        Throws an exception when an error occurs, and can
        be called again to resume the upload.
        """
        next_chunk_size = min(self.chunk_size, self.target_length - self.offset)
        if self.last_block == None:
            self.last_block = self.file_obj.read(next_chunk_size)

        try:
            (self.offset, self.upload_id) = self.client.upload_chunk(StringIO(self.last_block), next_chunk_size, self.offset, self.upload_id)
            self.last_block = None
        except rest.ErrorResponse, e:
            reply = e.body
            if "offset" in reply and reply['offset'] != 0:
                if reply['offset'] > self.offset:
                    self.last_block = None
                    self.offset = reply['offset']

class Downloader(threading.Thread):
    _itemsHandled = 0
    _itemsTotal = 0
    
    def __init__( self, client, path, location, isDir):
        super(Downloader, self).__init__()
        self.path = path
        self.remoteBasePath = os.path.dirname( path_from(path) )
        self.location = location
        self.isDir = isDir
        self._client = client
        self._fileList = Queue.Queue() #thread safe
        self._progress = xbmcgui.DialogProgress()
        self._progress.create(LANGUAGE_STRING(30039))
        self._progress.update( 0 )
        self.canceled = False

    def run(self):
        log_debug("Downloader started for: %s"%self.path)
        #First get all the file-items in the path
        if not self.isDir:
            #Download a single file
            item, changed = self._client.getMetaData(self.path)
            self._fileList.put( item )
        else:
            #Download a directory
            self.getFileItems(self.path)
        self._itemsTotal = self._fileList.qsize()
        #check if need to quit
        while not self._progress.iscanceled() and not self._fileList.empty():
            #Download the list of files/dirs
            item2Retrieve = self._fileList.get()
            if item2Retrieve:
                self._progress.update( (self._itemsHandled *100) / self._itemsTotal, LANGUAGE_STRING(30041), path_from(item2Retrieve['path']) )
                basePath = path_from(item2Retrieve['path'])
                basePath = basePath.replace(self.remoteBasePath, '', 1) # remove the remote base path
                location = self.location + basePath
                location = os.path.normpath(location)
                if item2Retrieve['is_dir']:
                    location += os.sep #add os seperator because it is a dir
                    #create dir if not present yet
                    if not xbmcvfs.exists( location.encode("utf-8") ):
                        xbmcvfs.mkdirs( location.encode("utf-8") )
                else:
                    if not self._client.saveFile(item2Retrieve['path'], location):
                        log_error("Downloader failed for: %s"%( path_from(item2Retrieve['path']) ) )
                self._itemsHandled += 1
            time.sleep(0.100)
        if self._progress.iscanceled():
            log_debug("Downloader stopped (as requested) for: %s"%self.path)
            self.canceled = True
        else:
            self._progress.update(100)
            log_debug("Downloader finished for: %s"%self.path)
        self._progress.close()
        del self._progress
        
    def getFileItems(self, path):
        items = self._client.getFolderContents(path)
        for item in items:
            self._fileList.put(item)
            if item['is_dir']:
                self.getFileItems( path_from(item['path']) )
