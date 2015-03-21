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


import xbmcgui
import xbmcvfs

import time
import threading
import shutil, os
import pickle

from resources.lib.utils import *
from resources.lib.dropboxclient import *
from resources.lib.sync.notifysync import NotifySyncServer
from resources.lib.sync.syncfolder import SyncFolder
from resources.lib.sync.syncthread import SynchronizeThread
from resources.lib.accountsettings import AccountSettings


class SyncAccount(object):
    '''
    The SyncAccount is a class that executes the synchronization of a account.
    The DropboxSynchronizer tells the SyncAccount when a synchronisation needs to be 
    done on user request or when settings of an account is changed.
    '''
    
    def __init__( self, account_name ):
        super(SyncAccount, self).__init__()
        self.account_name = account_name
        self._access_token = ''
        self._enabled = False
        self._syncPath = u''
        self._syncFreq = 0 #minutes
        self._newSyncTime = 0
        self._client = None
        self._clientCursor = None
        self.root = None
        self._remoteSyncPath = u'' #DROPBOX_SEP
        self.syncSemaphore = threading.Semaphore()
        self._storageFile = None
        self._sync_requests = []
        self._syncThread = None

    def init(self):
        # get sync settings
        self._get_settings()

    def stop_sync(self):
        if self._syncThread:
            self._syncThread.stop()

    def sync_stopped(self):
        stopped = True
        if self._syncThread:
            stopped = False
            if not self._syncThread.isAlive():
                #Done syncing, destroy the thread
                del self._syncThread
                self._syncThread = None
                stopped = True
        return stopped
        
    def check_sync(self):
        '''
        Check if it is time to sync according to the interval time.
        And do so when it is time to sync. 
        '''
        #check if syncing is in progress
        if self._enabled and self.sync_stopped():
            now = time.time()
            #Did we get sync requests or is it time to sync?
            if len(self._sync_requests) > 0 or self._newSyncTime < now:
                self._sync_requests = []
                if self._newSyncTime < now:
                    #update new sync time
                    self._updateSyncTime()
                if self._getClient(reconnect=True):
                    self._start_sync()
                else:
                    #No Client, try again after 5 secs?
                    pass

    def notify_sync_request(self, path):
        if self._enabled:
            self._sync_requests.append(path)

    def notify_changed_settings(self):
        self._get_settings()

    def remove_sync_data(self):
        # remove all sync data
        self.clearSyncData()
        if xbmcvfs.exists( self._syncPath.encode("utf-8") ):
            shutil.rmtree(self._syncPath)

    def _start_sync(self):
        #use a separate thread to do the syncing, so that the DropboxSynchronizer
        # can still handle other stuff (like changing settings) during syncing
        self._syncThread = SynchronizeThread(self)
        self._syncThread.start()

    def _get_settings( self ):
        account = AccountSettings(self.account_name)
        self._storageFile = os.path.normpath(account.account_dir + u'/sync_data.pik')
        gotSemaphore = True
        enable = account.synchronisation
        tempPath = account.syncpath
        tempRemotePath = account.remotepath
        tempFreq = float(account.syncfreq)
        #The following settings can't be changed while syncing!
        if not self.syncSemaphore.acquire(False):
            gotSemaphore = False
            settingsChanged = False
            if (enable != self._enabled) or (tempPath != self._syncPath) or (tempRemotePath != self._remoteSyncPath):
                log('Can\'t change settings while synchronizing for %s!' % (self.account_name) )
                dialog = xbmcgui.Dialog()
                stopSync = dialog.yesno(ADDON_NAME, LANGUAGE_STRING(30110), LANGUAGE_STRING(30113))
                if stopSync:
                    self.stop_sync() # stop the Synchronization
                    log('Synchronizing stopped for %s!' % (self.account_name) )
                    #wait for the semaphore to be released
                    self.syncSemaphore.acquire()
                    gotSemaphore = True
                else:
                    #revert the changes
                    account.synchronisation = self._enabled
                    account.syncpath = self._syncPath
                    account.remotepath = self._remoteSyncPath
                    account.save()
                    return
        #Enable?
        if enable and (tempPath == '' or tempRemotePath == ''):
            enable = False
            account.synchronisation = False
            account.save()
            log_error('Can\'t enable synchronization: syncpath or remotepath not set!')
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30111))
        self._enabled = enable
        if self._syncPath == u'':
            #get initial location
            self._syncPath = tempPath
        #Sync path changed?
        if self._syncPath != tempPath:
            if len(os.listdir(tempPath)) == 0:
                if xbmcvfs.exists(self._syncPath.encode("utf-8")):
                    #move the old sync path to the new one
                    log('Moving sync location for %s from %s to %s'%(self.account_name, self._syncPath, tempPath))
                    names = os.listdir(self._syncPath)
                    for name in names:
                        srcname = os.path.join(self._syncPath, name)
                        shutil.move(srcname, tempPath)
                self._syncPath = tempPath
                if self.root:
                    self.root.updateLocalRootPath(self._syncPath)
                log('SyncPath updated for %s' % (self.account_name) )
                xbmc.executebuiltin('Notification(%s,%s,%d,%s)' % (LANGUAGE_STRING(30103), tempPath, 7000, ICON))
            else:
                log_error('New sync location is not empty: %s'%(tempPath))
                dialog = xbmcgui.Dialog()
                dialog.ok(ADDON_NAME, LANGUAGE_STRING(30104), tempPath)
                #restore the old location
                account.syncpath = self._syncPath
                account.save()
        if self._remoteSyncPath == '':
            #get initial location
            self._remoteSyncPath = tempRemotePath
        #remote path changed?
        if tempRemotePath != self._remoteSyncPath:
            self._remoteSyncPath = tempRemotePath
            log('Changed remote path for %s to %s'%(self.account_name, self._remoteSyncPath))
            if self.root:
                #restart the synchronization 
                #remove all the files in current syncPath
                if xbmcvfs.exists(self._syncPath.encode("utf-8")) and len(os.listdir(self._syncPath)) > 0:
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
        self._access_token = account.access_token
        self._getClient(reconnect=True)
        if self._enabled and not self.root:
            log('Enabled synchronization for %s' % (self.account_name) )
            self._setupSyncRoot()
        elif not self._enabled and self.root:
            log('Disabled synchronization for %s' % (self.account_name) )
            self._syncFreq = 0 # trigger a sync next time it is enabled again
            self.stop_sync()
            del self.root
            self.root = None
        if gotSemaphore:
            self.syncSemaphore.release()

    def _getClient(self, reconnect=False):
        if reconnect and self._client:
            self._client.disconnect()
            self._client = None
        if not self._client:
            self._client = XBMCDropBoxClient(autoConnect=False, access_token=self._access_token)
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
                    if isinstance(path, str):
                        #perviously stored as str iso. unicode... So make it unicode now.
                        path = path.decode("utf-8")
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
            log("Opening storageFile EXCEPTION : %s" %(repr(e)) )
        return cursor, data

    def clearSyncData(self):
        self._clientCursor = None
        try:
            os.remove(self._storageFile)
        except OSError as e:
            log("Removing storageFile EXCEPTION : %s" %(repr(e)) )

