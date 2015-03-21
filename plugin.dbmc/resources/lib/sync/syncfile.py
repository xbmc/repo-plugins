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

import xbmcvfs

import os, traceback

from stat import *

from resources.lib.utils import *
from resources.lib.sync.syncobject import SyncObject

class SyncFile(SyncObject):
    
    def __init__( self, path, client):
        log_debug('Create SyncFile: %s'%path)
        super(SyncFile, self).__init__(path, client)

    def inSync(self):
        if self._state == self.OBJECT_SKIP:
            log_debug('Skipping file: %s'%self._localPath)
            return self.OBJECT_IN_SYNC #fake object in sync...
        localPresent = False
        if self._localPath:
            localPresent = xbmcvfs.exists(self._localPath.encode("utf-8"))
        elif self._remotePresent:
            log_error("Has no localPath! %s"%self.path)
        localTimeStamp = 0
        if localPresent:
            st = os.stat(self._localPath)
            localTimeStamp = st[ST_MTIME]
        #File present
        if not localPresent and self._remotePresent:
            return self.OBJECT_2_DOWNLOAD
        if not self._remotePresent:
            if localPresent:
                return self.OBJECT_2_REMOVE
#                 #Check if local file is a newer one than the old remote file
#                 # if so, use the new local file...
#                 if localTimeStamp > self._localTimeStamp:
#                     return self.OBJECT_2_UPLOAD
#                 else:
#                     return self.OBJECT_2_REMOVE
            else:
                #File is completely removed, so can be removed from memory as well
                return self.OBJECT_REMOVED
        #compair time stamps
        if self._newRemoteTimeStamp > self._remoteTimeStamp:
            return self.OBJECT_2_DOWNLOAD
#                 #Check if local file is a newer one than the new remote file
#                 # if so, use the new local file...
#                 if localTimeStamp > self._localTimeStamp and localTimeStamp > self._remoteTimeStamp:
#                     return self.OBJECT_2_UPLOAD
#                 else:
#                     return self.OBJECT_2_DOWNLOAD
#         if localTimeStamp > self._localTimeStamp:
#             return self.OBJECT_2_UPLOAD
        return self.OBJECT_IN_SYNC
        
    def sync(self):
        if self._state == self.OBJECT_SKIP:
            return
        try:
            self._state = self.inSync()
            if self._state == self.OBJECT_2_DOWNLOAD:
                log_debug('Download file to: %s'%self._localPath)
                self._client.saveFile(self.path, self._localPath)
                self.updateTimeStamp()
            elif self._state == self.OBJECT_2_UPLOAD:
                log_debug('Upload file: %s'%self._localPath)
                self._client.upload(self._localPath, self.path)
                st = os.stat(self._localPath)
                self._localTimeStamp = st[ST_MTIME] 
            elif self._state == self.OBJECT_2_REMOVE:
                log_debug('Removing file: %s'%self._localPath)
                os.remove(self._localPath)
            elif self._state == self.OBJECT_IN_SYNC or self._state == self.OBJECT_REMOVED:
                pass
            else:
                log_error('Unknown file status(%s) for: %s!'%(self._state, self.path))
        except Exception, e:
            log_error('Exception occurred for file %s' % self._localPath)
            log_error( traceback.format_exc() )
            if(self._failure):
                #failure happened before... So skip this item in all the next syncs!
                self._state = self.OBJECT_SKIP
                log_error('Skipping file in next syncs: %s'% self._localPath)
            self._failure = True
    
    def setItemInfo(self, path, meta):
        if path == self.path:
            super(SyncFile, self).setItemInfo(meta)
        else:
            log_error('setItemInfo() item with wrong path: %s should be: %s'%(path, self.path))

    def updateRemoteInfo(self, path, meta):
        if path == self.path:
            super(SyncFile, self).updateRemoteInfo(meta)
        else:
            log_error('updateRemoteInfo() item with wrong path: %s should be: %s'%(path, self.path))

    def setClient(self, client):
        self._client = client
