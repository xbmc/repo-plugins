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

import xbmcplugin
import xbmcgui
import xbmcvfs

import time, datetime
import threading
import shutil, os
from stat import *
import pickle

from resources.lib.utils import *
from resources.lib.dropboxclient import *
from resources.lib.notifysync import *

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

class DropboxSynchronizer:
    
    def __init__( self ):
        self._enabled = False
        self._syncPath = ''
        self._syncFreq = 0 #minutes
        self._newSyncTime = 0
        self._client = None
        self._clientCursor = None
        self.root = None
        self._remoteSyncPath = '' #DROPBOX_SEP
        self._notified = None
        self.syncSemaphore = threading.Semaphore()
        self._syncThread = None
        dataPath = xbmc.translatePath( ADDON.getAddonInfo('profile') )
        self._storageFile = dataPath + '/sync_data.pik'

    def run(self):
        # start daemon
        xbmc.sleep(10000) #wait for CommonCache to startup
        #self.clearSyncData()
        # get addon settings
        self._get_settings()
        while (not xbmc.abortRequested):
            if self._enabled:
                if not self._notified:
                    self._notified = NotifySyncServer()
                    self._notified.start()
                now = time.time()
                #get remote sync requests
                syncRequests = self._notified.getNotification()
                if len(syncRequests) > 0 or self._newSyncTime < now:
                    if self._getClient(reconnect=True):
                        if self._newSyncTime < now:
                            #update new sync time
                            self._updateSyncTime()
                        log_debug('Start sync...')
                        #use a separate thread to do the syncing, so that the DropboxSynchronizer
                        # can still handle other stuff (like changing settings) during syncing
                        self._syncThread = SynchronizeThread(self)
                        self._syncThread.start()
                        while self._syncThread.isAlive():
                            if xbmc.abortRequested:
                                self._syncThread.stop()
                            xbmc.sleep(100)
                        del self._syncThread
                        self._syncThread = None
                        if not xbmc.abortRequested:
                            log_debug('Finished sync...')
                        else:
                            log('DropboxSynchronizer: Sync aborted...')
                    else:
                        #No Client, try again after 5 secs
                        xbmc.sleep(5000)
                else:
                    #No sync needed yet
                    xbmc.sleep(1000) #1 secs
            else:
                #not enabled
                xbmc.sleep(1000) #1 secs
        if self._notified:
            self._notified.closeServer()

    def _get_settings( self ):
        gotSemaphore = True
        enable = ('true' == ADDON.getSetting('synchronisation').lower())
        tempPath = ADDON.getSetting('syncpath')
        tempRemotePath = ADDON.getSetting('remotepath')
        tempFreq = float( ADDON.getSetting('syncfreq') )
        #The following settings can't be changed while syncing!
        if not self.syncSemaphore.acquire(False):
            gotSemaphore = False
            settingsChanged = False
            if (enable != self._enabled) or (tempPath != self._syncPath) or (tempRemotePath != self._remoteSyncPath):
                log('Can\'t change settings while synchronizing!')
                dialog = xbmcgui.Dialog()
                stopSync = dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30110), LANGUAGE_STRING(30113))
                if stopSync:
                    if self._syncThread: #should always be true, but just in case check...
                        self._syncThread.stop()
                    log('Synchronizing stopped!')
                    #wait for the semaphore to be released
                    self.syncSemaphore.acquire()
                    gotSemaphore = True
                else:
                    #revert the changes
                    if self._enabled:
                        enabledStr = 'true'
                    else:
                        enabledStr = 'false'
                    ADDON.setSetting('synchronisation', enabledStr)
                    ADDON.setSetting('syncpath', self._syncPath)
                    ADDON.setSetting('remotepath', self._remoteSyncPath)
                    return
        #Enable?
        if enable and (tempPath == '' or tempRemotePath == ''):
            enable = False
            ADDON.setSetting('synchronisation', 'false')
            log_error('Can\'t enable synchronization: syncpath or remotepath not set!')
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30111))
        self._enabled = enable
        if self._syncPath == '':
            #get initial location
            self._syncPath = tempPath
        #Sync path changed?
        if self._syncPath != tempPath:
            if len(os.listdir(tempPath)) == 0:
                if xbmcvfs.exists(self._syncPath):
                    #move the old sync path to the new one
                    log('Moving sync location from %s to %s'%(self._syncPath, tempPath))
                    names = os.listdir(self._syncPath)
                    for name in names:
                        srcname = os.path.join(self._syncPath, name)
                        shutil.move(srcname, tempPath)
                self._syncPath = tempPath
                if self.root:
                    self.root.updateLocalRootPath(self._syncPath)
                log('SyncPath updated')
                xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE_STRING(30103), tempPath, 7000))
            else:
                log_error('New sync location is not empty: %s'%(tempPath))
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30104), tempPath)
                #restore the old location
                ADDON.setSetting('syncpath', self._syncPath)
        if self._remoteSyncPath == '':
            #get initial location
            self._remoteSyncPath = tempRemotePath
        #remote path changed?
        if tempRemotePath != self._remoteSyncPath:
            self._remoteSyncPath = tempRemotePath
            log('Changed remote path to %s'%(self._remoteSyncPath))
            if self.root:
                #restart the synchronization 
                #remove all the files in current syncPath
                if xbmcvfs.exists(self._syncPath) and len(os.listdir(self._syncPath)) > 0:
                    shutil.rmtree(self._syncPath)
                #reset the complete data on client side
                self.clearSyncData()
                del self.root
                self.root = None
                #Start sync immediately
                self._newSyncTime = time.time()
        #Time interval changed?
        self._updateSyncTime(tempFreq)
        #reconnect to Dropbox (in case the token has changed)
        self._getClient(reconnect=True)
        if self._enabled and not self.root:
            log('Enabled synchronization')
            self._setupSyncRoot()
        elif not self._enabled and self.root:
            log('Disabled synchronization')
            self._notified.closeServer()
            del self._notified
            self._notified = None
            del self.root
            self.root = None
        # re-init when settings have changed
        self.monitor = SettingsMonitor(callback=self._get_settings)
        if gotSemaphore:
            self.syncSemaphore.release()

    def _getClient(self, reconnect=False):
        if reconnect and self._client:
            self._client.disconnect()
            self._client = None
        if not self._client:
            self._client = XBMCDropBoxClient(autoConnect=False)
            succes, msg = self._client.connect()
            if not succes:
                log_error('DropboxSynchronizer could not connect to dropbox: %s'%(msg))
                self._client = None
            #update changed client to the root syncfolder
            if self.root:
                self.root.setClient(self._client)
        return self._client
        
    def _updateSyncTime(self, newFreq = None):
        if newFreq and self._syncFreq == 0:
            #trigger initial sync after startup
            self._newSyncTime = time.time()
            self._syncFreq = newFreq
        else:
            update = False
            if newFreq == None:
                update = True
            elif self._syncFreq != newFreq:
                self._syncFreq = newFreq
                update = True
            if update:
                freqSecs = self._syncFreq * 60
                now = time.time()
                self._newSyncTime = float(freqSecs * round(float(now)/freqSecs))
                if self._newSyncTime < now:
                    self._newSyncTime += freqSecs
                log_debug('New sync time: %s'%( time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(self._newSyncTime) ) ) )
    
    def _setupSyncRoot(self):
        self.createSyncRoot()
        #Update items which are in the cache
        clientCursor = self.getClientCursor()
        if clientCursor:
            log_debug('Setup SyncRoot with stored remote data')
            cursor, remoteData = self.getSyncData()
            if remoteData:
                for path, meta in remoteData.iteritems():
                    if path.find(self.root.path) == 0:
                        self.root.setItemInfo(path, meta)
                self.root.updateLocalRootPath(self._syncPath)
            else:
                log_error('Remote cursor present, but no remote data!')
    
    def createSyncRoot(self):
        #Root path is _remoteSyncPath but then with lower case!
        self.root = SyncFolder(self._remoteSyncPath.lower(), self._client)

    def getClientCursor(self):
        if self._clientCursor == None:
            #try to get the cursor from storage
            cursor, data = self.getSyncData()
            if cursor != None:
                log_debug('Using stored remote cursor')
                self._clientCursor = cursor
        return self._clientCursor

    def storeSyncData(self, cursor=None):
        data = None
        if self.root:
            data = self.root.getItemsInfo()
        if cursor != None:
            self._clientCursor = cursor
        log_debug('Storing sync data')
        try:
            with open(self._storageFile, 'w') as f:
                pickle.dump([self._clientCursor, data], f, -1)
        except EnvironmentError as e:
            log_error("Storing storageFile EXCEPTION : %s" %(repr(e)) )

    def getSyncData(self):
        data = None
        cursor = None
        try:
            with open(self._storageFile, 'r') as f:
                cursor, data = pickle.load(f)
        except EnvironmentError as e:
            log_error("Opening storageFile EXCEPTION : %s" %(repr(e)) )
        return cursor, data

    def clearSyncData(self):
        self._clientCursor = None
        try:
            os.remove(self._storageFile)
        except OSError as e:
            log_error("Removing storageFile EXCEPTION : %s" %(repr(e)) )

class SynchronizeThread(threading.Thread):
    PROGRESS_TIMEOUT = 20.0
    
    def __init__(self, dropboxSyncer):
        super(SynchronizeThread, self).__init__()
        self._stop = False
        self._dropboxSyncer = dropboxSyncer
        self._lastProgressUpdate = 0.0
    
    def stop(self):
        self._stop = True

    def run(self):
        self._dropboxSyncer.syncSemaphore.acquire()
        self._getRemoteChanges()
        if not self._stop:
            self._synchronize()
        self._dropboxSyncer.syncSemaphore.release()

    def _getRemoteChanges(self):
        hasMore = True
        clientCursor = self._dropboxSyncer.getClientCursor()
        initalSync = False
        if clientCursor == None:
            initalSync = True
            log('Starting first sync...')
        while hasMore and not self._stop:
            #Sync, get all metadata
            items, clientCursor, reset, hasMore = self._dropboxSyncer._client.getRemoteChanges(clientCursor)
            if reset:
                #reset the complete data on client side
                log('Reset requested from remote server...')
                self._dropboxSyncer.clearSyncData()
                del self._dropboxSyncer.root
                #Root path is _remoteSyncPath but then with lower case!
                self._dropboxSyncer.createSyncRoot()
                initalSync = True
            #prepare item list
            for path, meta in items.iteritems():
                if not initalSync:
                    log_debug('New item info received for %s'%(path) )
                if path.find(self._dropboxSyncer.root.path) == 0:
                    self._dropboxSyncer.root.updateRemoteInfo(path, meta)
            if len(items) > 0:
                self._dropboxSyncer.root.updateLocalRootPath(self._dropboxSyncer._syncPath)
            #store new cursor + data
            self._dropboxSyncer.storeSyncData(clientCursor)

    def _synchronize(self):
        #Get the items to sync
        syncDirs, syncItems = self._dropboxSyncer.root.getItems2Sync()
        #alsways first sync(create) dirs, so that they will have the correct time stamps
        if (len(syncItems) > 0) or (len(syncDirs) > 0):
            for dir in syncDirs:
                if self._stop:
                    break #exit for loop
                dir.sync()
            itemsTotal = len(syncItems)
            if itemsTotal > 0 and not self._stop:
                itemNr = 0
                for item in syncItems:
                    if self._stop:
                        break #exit for loop
                    else:
                        self.updateProgress(itemNr, itemsTotal)
                        item.sync()
                        itemNr += 1
                self.updateProgressFinished(itemNr, itemsTotal)
            #store the new data
            self._dropboxSyncer.storeSyncData()

    def updateProgress(self, handled, total):
        now = time.time()
        if (self._lastProgressUpdate + self.PROGRESS_TIMEOUT) < now:
            log('Synchronizing number of items: %s/%s' % (handled, total) )
            xbmc.executebuiltin('Notification(%s,%s,%i)' % (LANGUAGE_STRING(30114), str(handled)+'/'+str(total), 7000))
            self._lastProgressUpdate = now
            #Also store the new data (frequently)
            self._dropboxSyncer.storeSyncData()

    def updateProgressFinished(self, handled, total):
        log('Number of items synchronized: %s' % (handled) )
        xbmc.executebuiltin('Notification(%s,%s%s,%i)' % (LANGUAGE_STRING(30106), LANGUAGE_STRING(30107), handled, 7000))
            

class SyncObject(object):
    OBJECT_IN_SYNC = 0
    OBJECT_2_DOWNLOAD = 1
    OBJECT_2_UPLOAD = 2
    OBJECT_2_REMOVE = 3
    OBJECT_ADD_CHILD = 4
    OBJECT_REMOVED = 5
    
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

    def setItemInfo(self, meta):
        log_debug('Set stored metaData: %s'%self.path)
        if meta:
            if self.path != string_path(meta['path']):
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
                self._name = string_path(meta['name'])
            elif 'Path' in meta:
                #for backwards compatibility (v0.6.2)
                self._name = os.path.basename((string_path(meta['Path'])))
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
            self._name = os.path.basename((string_path(meta['path']))) # get the case-sensitive name!
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
            #decode the _localPath to 'utf-8'
            # in windows os.stat() only works with unicode...
            self._localPath = os.path.normpath(parentSyncPath + os.sep + self._name).decode("utf-8")

class SyncFile(SyncObject):
    
    def __init__( self, path, client):
        log_debug('Create SyncFile: %s'%path)
        super(SyncFile, self).__init__(path, client)

    def inSync(self):
        localPresent = False
        if self._localPath:
            localPresent = xbmcvfs.exists(self._localPath)
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
        fileStatus = self.inSync()
        if fileStatus == self.OBJECT_2_DOWNLOAD:
            log_debug('Download file to: %s'%self._localPath)
            self._client.saveFile(self.path, self._localPath)
            self.updateTimeStamp()
        elif fileStatus == self.OBJECT_2_UPLOAD:
            log_debug('Upload file: %s'%self._localPath)
            self._client.upload(self._localPath, self.path)
            st = os.stat(self._localPath)
            self._localTimeStamp = st[ST_MTIME] 
        elif fileStatus == self.OBJECT_2_REMOVE:
            log_debug('Removing file: %s'%self._localPath)
            os.remove(self._localPath)
        elif fileStatus == self.OBJECT_IN_SYNC or fileStatus == self.OBJECT_REMOVED:
            pass
        else:
            log_error('Unknown file status(%s) for: %s!'%(fileStatus, self.path))
    
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
        localPresent = False
        if self._localPath:
            localPresent = xbmcvfs.exists(self._localPath)
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
        folderStatus = self.inSync() 
        if folderStatus == self.OBJECT_2_DOWNLOAD:
            log_debug('Create folder: %s'%self._localPath)
            xbmcvfs.mkdirs( self._localPath )
            self.updateTimeStamp()
        elif folderStatus == self.OBJECT_2_UPLOAD:
            log_error('Can\'t upload folder: %s'%self._localPath)
            #TODO Add files if new files found local
            #TODO: modify timestamp of dir...
        elif folderStatus == self.OBJECT_2_REMOVE:
            log_debug('Remove folder: %s'%self._localPath)
            shutil.rmtree(self._localPath)
        elif folderStatus == self.OBJECT_ADD_CHILD:
            #TODO
            pass
        elif folderStatus == self.OBJECT_IN_SYNC:
            pass
        else:
            log_error('Unknown folder status(%s) for : %s!'%(folderStatus, self.path))
            
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
        for path, child in self._children.iteritems():
            child.updateLocalPath(parentSyncPath + os.sep + self._name)

    def updateLocalRootPath(self, syncPath):
        #don't add the self._name to the syncpath for root!
        self._localPath = os.path.normpath(syncPath).decode("utf-8")
        for path, child in self._children.iteritems():
            child.updateLocalPath(syncPath)


class SettingsMonitor(xbmc.Monitor):
    def __init__( self, callback ):
        xbmc.Monitor.__init__( self )
        self.callback = callback

    def onSettingsChanged( self ):
        log_debug('SettingsMonitor: onSettingsChanged()')
        # sleep before retrieving the new settings
        xbmc.sleep(500)
        self.callback()
 
if ( __name__ == "__main__" ):
    log_debug('sync_dropbox.py: Argument List: %s' % str(sys.argv))
    log('DropboxSynchronizer started')
    sync = DropboxSynchronizer()
    sync.run()
    log('DropboxSynchronizer ended')
