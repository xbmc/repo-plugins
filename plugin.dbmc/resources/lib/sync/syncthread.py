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

import threading

from resources.lib.utils import *

class SynchronizeThread(threading.Thread):
    PROGRESS_TIMEOUT = 20.0
    
    def __init__(self, sync_account):
        super(SynchronizeThread, self).__init__()
        self._stop = False
        self._sync_account = sync_account
        self._lastProgressUpdate = 0.0
    
    def stop(self):
        self._stop = True

    def run(self):
        log_debug('Start sync for account %s...' % (self._sync_account.account_name) )
        self._sync_account.syncSemaphore.acquire()
        self._getRemoteChanges()
        if not self._stop:
            self._synchronize()
        self._sync_account.syncSemaphore.release()
        if self._stop:
            log('DropboxSynchronizer: Sync aborted account %s...'% (self._sync_account.account_name))
        else:
            log_debug('Finished sync account %s...'% (self._sync_account.account_name))

    def _getRemoteChanges(self):
        hasMore = True
        clientCursor = self._sync_account.getClientCursor()
        initalSync = False
        if clientCursor == None:
            initalSync = True
            log('Starting first sync...')
        while hasMore and not self._stop:
            #Sync, get all metadata
            items, clientCursor, reset, hasMore = self._sync_account._client.getRemoteChanges(clientCursor)
            if reset:
                #reset the complete data on client side
                log('Reset requested from remote server...')
                self._sync_account.clearSyncData()
                del self._sync_account.root
                #Root path is _remoteSyncPath but then with lower case!
                self._sync_account.createSyncRoot()
                initalSync = True
            #prepare item list
            for path, meta in items.iteritems():
                if not initalSync:
                    log_debug('New item info received for %s'%(path) )
                if path.find(self._sync_account.root.path) == 0:
                    self._sync_account.root.updateRemoteInfo(path, meta)
            if len(items) > 0:
                self._sync_account.root.updateLocalRootPath(self._sync_account._syncPath)
            #store new cursor + data
            self._sync_account.storeSyncData(clientCursor)

    def _synchronize(self):
        #Get the items to sync
        syncDirs, syncItems = self._sync_account.root.getItems2Sync()
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
            self._sync_account.storeSyncData()

    def updateProgress(self, handled, total):
        now = time.time()
        if (self._lastProgressUpdate + self.PROGRESS_TIMEOUT) < now:
            progress_text = u'%s/%s (%s)' % (str(handled), str(total), self._sync_account.account_name)
            log('Synchronizing number of items: ' + progress_text )
            buildin = u'Notification(%s,%s,%d,%s)' % (LANGUAGE_STRING(30114).decode("utf-8"), progress_text, 7000, ICON.decode("utf-8"))
            xbmc.executebuiltin(buildin.encode("utf-8"))
            self._lastProgressUpdate = now
            #Also store the new data (frequently)
            self._sync_account.storeSyncData()

    def updateProgressFinished(self, handled, total):
        progress_text = u'%s (%s)' % (str(handled), self._sync_account.account_name)
        log('Number of items synchronized: ' + progress_text )
        buildin = u'Notification(%s,%s%s,%d,%s)' % (LANGUAGE_STRING(30106).decode("utf-8"), LANGUAGE_STRING(30107).decode("utf-8"), progress_text, 10000, ICON.decode("utf-8"))
        xbmc.executebuiltin(buildin.encode("utf-8"))
