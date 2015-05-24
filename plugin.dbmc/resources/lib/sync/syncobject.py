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
import os

from stat import *

from resources.lib.utils import *
from resources.lib.dropboxclient import *

class SyncObject(object):
    OBJECT_IN_SYNC = 0
    OBJECT_2_DOWNLOAD = 1
    OBJECT_2_UPLOAD = 2
    OBJECT_2_REMOVE = 3
    OBJECT_ADD_CHILD = 4
    OBJECT_REMOVED = 5
    OBJECT_SKIP = 6
    
    def __init__(self, path, client):
        #note: path is case-insensitive, meta['path'] is case-sensitive
        self.path = path #case-insensitive path
        self.isDir = False
        self._name = None #case-sensitive item name
        self._client = client
        self._localPath = None
        self._remotePresent = True
        self._remoteTimeStamp = 0
        self._remoteClientModifiedTime = 0
        self._newRemoteTimeStamp = 0
        self._localTimeStamp = 0
        self._failure = False
        self._state = self.OBJECT_IN_SYNC

    def setItemInfo(self, meta):
        log_debug('Set stored metaData: %s'%self.path)
        if meta:
            if self.path != path_from(meta['path']):
                log_error('Stored metaData path(%s) not equal to path %s'%(meta['path'], self.path) )
            if 'present' in meta:
                self._remotePresent = meta['present']
            if 'local_mtime' in meta:
                self._localTimeStamp = meta['local_mtime']
            if 'remote_mtime' in meta:
                self._remoteTimeStamp = meta['remote_mtime']
                self._newRemoteTimeStamp = self._remoteTimeStamp
            if 'client_mtime' in meta:
                self._remoteClientModifiedTime = meta['client_mtime']
            if 'name' in meta:
                self._name = path_from(meta['name'])
            elif 'Path' in meta:
                #for backwards compatibility (v0.6.2)
                self._name = os.path.basename((path_from(meta['Path'])))
        else:
            self._remotePresent = False
        
    def getItemInfo(self):
        meta = {}
        meta['path'] = self.path
        meta['name'] = self._name
        meta['is_dir'] = self.isDir
        meta['present'] = self._remotePresent
        meta['local_mtime'] = self._localTimeStamp
        meta['remote_mtime'] = self._remoteTimeStamp
        meta['client_mtime'] = self._remoteClientModifiedTime
        return meta

    def updateRemoteInfo(self, meta):
        log_debug('Update remote metaData: %s'%self.path)
        if meta:
            self._name = os.path.basename((path_from(meta['path']))) # get the case-sensitive name!
            #convert to local time 'Thu, 28 Jun 2012 17:55:59 +0000',
            time_struct = time.strptime(meta['modified'], '%a, %d %b %Y %H:%M:%S +0000')
            self._newRemoteTimeStamp = utc2local( time.mktime(time_struct) )
            if 'client_mtime' in meta:
                time_struct = time.strptime(meta['client_mtime'], '%a, %d %b %Y %H:%M:%S +0000')
                self._remoteClientModifiedTime = utc2local( time.mktime(time_struct) )
        else:
            log_debug('Item removed on remote: %s'%self.path)
            self._remotePresent = False
            #keep remote/local time to compair lateron         
            #self._remoteTimeStamp = 0
            #self._localTimeStamp = 0
            
    def updateTimeStamp(self):
        #local modified time = client_mtime
        st = os.stat(self._localPath)
        atime = st[ST_ATIME] #access time
        mtime = st[ST_MTIME] #modification time
        #modify the file timestamp
        os.utime(self._localPath, (atime, int(self._remoteClientModifiedTime) ))
        #read back and store the local timestamp value
        # this is used for comparison to the remote modified time
        st = os.stat(self._localPath)
        self._localTimeStamp = st[ST_MTIME]
        self._remoteTimeStamp = self._newRemoteTimeStamp
        
    def updateLocalPath(self, parentSyncPath):
        #Note: self.path should be the case-sensitive path by now!
        if self._name:
            self._localPath = os.path.normpath(parentSyncPath + self._name)

