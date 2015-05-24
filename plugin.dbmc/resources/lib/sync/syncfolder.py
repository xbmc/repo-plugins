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

import shutil, os, traceback

from resources.lib.utils import *
from resources.lib.sync.syncobject import SyncObject
from resources.lib.sync.syncfile import SyncFile

class SyncFolder(SyncObject):

    def __init__( self, path, client):
        log_debug('Create SyncFolder: %s'%path)
        super(SyncFolder, self).__init__(path, client)
        self.isDir = True
        self._children = {}

    def setItemInfo(self, path, meta):
        if path == self.path:
            super(SyncFolder, self).setItemInfo(meta)
        elif path.find(self.path) != 0:
            log_error('setItemInfo() Item(%s) isn\'t part of the remote sync path(%s)'%(path, self.path))            
            return
        else:
            child = self.getItem(path, meta)
            child.setItemInfo(path, meta)

    def updateRemoteInfo(self, path, meta):
        if path == self.path:
            super(SyncFolder, self).updateRemoteInfo(meta)
        elif path.find(self.path) != 0:
            log_error('updateRemoteInfo() Item(%s) isn\'t part of the remote sync path(%s)'%(path, self.path))            
            return
        else:
            child = self.getItem(path, meta)
            child.updateRemoteInfo(path, meta)
            
    def getItemsInfo(self):
        metaDataList = {}
        metaDataList[self.path] = self.getItemInfo()
        for path, child in self._children.iteritems():
            if child.isDir:
                childMetaData = child.getItemsInfo()
                metaDataList.update( childMetaData )
            else:
                metaDataList[path] = child.getItemInfo()
        return metaDataList
        
    def getItem(self, path, meta):
        #strip the child name
        #exclude it's own path from the search for the first seperator
        end = path.find(DROPBOX_SEP, len(self.path)+1)
        isDir = True
        if end > 0:
            #it wasn't my own child so create the new folder and search/update that one
            childPath = path[:end]
        elif meta and meta['is_dir']:
            #it is my child and it is a folder
            childPath = path
        else:
            #it is my child and it is a file
            childPath = path
            isDir = False
        if not(childPath in self._children):
            #create the child
            if isDir:
                child = SyncFolder(childPath, self._client)
            else:
                child = SyncFile(childPath, self._client)
            #add the new created child to the childern's list
            self._children[childPath] = child
        return self._children[childPath]

    def inSync(self):
        if self._state == self.OBJECT_SKIP:
            log_debug('Skipping folder: %s'%self._localPath)
            return self.OBJECT_IN_SYNC #fake object in sync...
        localPresent = False
        if self._localPath:
            localPresent = xbmcvfs.exists(self._localPath.encode("utf-8"))
        elif self._remotePresent:
            log_error("Has no localPath! %s"%self.path)
        #File present
        if not localPresent and self._remotePresent:
            return self.OBJECT_2_DOWNLOAD
        if not self._remotePresent:
            if localPresent:
                #TODO check if local file is a newer one than the old remote file
                # if so, use the new local file...
                return self.OBJECT_2_REMOVE
            else:
                #File is completely removed, so can be removed from memory as well
                return self.OBJECT_REMOVED
        #TODO Check if files are present on disk but not in it's 
        # _childern's list
        #return self.OBJECT_ADD_CHILD
        return self.OBJECT_IN_SYNC
        
    def sync(self):
        if self._state == self.OBJECT_SKIP:
            return
        try:
            self._state = self.inSync() 
            if self._state == self.OBJECT_2_DOWNLOAD:
                log_debug('Create folder: %s'%self._localPath)
                xbmcvfs.mkdirs( self._localPath.encode("utf-8") )
                self.updateTimeStamp()
            elif self._state == self.OBJECT_2_UPLOAD:
                log_error('Can\'t upload folder: %s'%self._localPath)
                #TODO Add files if new files found local
                #TODO: modify timestamp of dir...
            elif self._state == self.OBJECT_2_REMOVE:
                log_debug('Remove folder: %s'%self._localPath)
                shutil.rmtree(self._localPath)
            elif self._state == self.OBJECT_ADD_CHILD:
                #TODO
                pass
            elif self._state == self.OBJECT_IN_SYNC:
                pass
            else:
                log_error('Unknown folder status(%s) for : %s!'%(self._state, self.path))
        except Exception, e:
            log_error('Exception occurred for folder %s' % self._localPath)
            log_error( traceback.format_exc() )
            if(self._failure):
               #failure happened before... So skip this item in all the next syncs!
                self._state = self.OBJECT_SKIP
                log_error('Skipping folder in next syncs: %s'% self._localPath)
            self._failure = True

    def getItems2Sync(self):
        dirs2Sync = []
        items2Sync = []
        removeList = {}
        for path, child in self._children.iteritems():
            if child.isDir:
                newDirs, newItems = child.getItems2Sync()
                dirs2Sync += newDirs
                items2Sync += newItems
            childSyncStatus = child.inSync()
            if childSyncStatus == child.OBJECT_REMOVED:
                #Remove child from list
                removeList[path] = child
            elif childSyncStatus != child.OBJECT_IN_SYNC:
                if child.isDir:
                    dirs2Sync.append(child)
                else:
                    items2Sync.append(child)
        #Remove child's from list (this we can do now)
        if len(removeList) > 0:
            #sync this dir (dummy sync to remove the deleted child from storage)
            dirs2Sync.append(self)
        for path in removeList:
            child = self._children.pop(path) 
            del child
        return dirs2Sync, items2Sync
    
    def setClient(self, client):
        self._client = client
        for child in self._children.itervalues():
            child.setClient(client)

    def updateLocalPath(self, parentSyncPath):
        super(SyncFolder, self).updateLocalPath(parentSyncPath)
        #_localpath can be None when the _name also is None
        #This can happen when the folder was deleted on dropbox 
        # before it was ever on this system and dropbox doesn't update the meta data...
        if self._localPath: 
            #for folders add the os seperator (xbmcvfs.exists() needs it) 
            self._localPath += os.sep
            for path, child in self._children.iteritems():
                child.updateLocalPath(self._localPath)

    def updateLocalRootPath(self, syncPath):
        #don't add the self._name to the syncpath for root!
        self._localPath = os.path.normpath(syncPath)
        self._localPath += os.sep
        for path, child in self._children.iteritems():
            child.updateLocalPath(self._localPath)
