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

import socket
import threading, Queue
import json

from resources.lib.utils import *

HOST = '127.0.0.1' #use 127.0.0.1 needed for windows
PORT = 0 #Let OS get a free port
SOCKET_BUFFER_SIZE = 1024

NOTIFY_SYNC_PATH = 'sync_path'
NOTIFY_CHANGED_ACCOUNT = 'account_settings_changed'
NOTIFY_ADDED_REMOVED_ACCOUNT = 'account_added_removed'

class NotifySyncServer(threading.Thread):
    '''
    The NotifySyncServer listens to a TCP port to check if a NotifySyncClient
    reported a change event. A change event can be send by a client (DMBC plugin)
    when something changes on the synced folder.
    This NotifySyncServer is started by the DropboxSynchronizer. And DropboxSynchronizer
    will check the NotifySyncServer to see if it should perform a sync.
    ''' 
    
    def __init__(self):
        super(NotifySyncServer, self).__init__()
        self._socket = None
        self._stop = False
        self._usedPort = 0
        self._notifyList = Queue.Queue() #thread safe
        
    def setupServer(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._socket.bind( (HOST, PORT) )
            self._usedPort = self._socket.getsockname()[1]
            self._socket.listen(1)
        except Exception as e:
            log_error("NotifySyncServer failed to bind to socket: %s" %(repr(e)) )
            self._socket.close()
            self._socket = None
            self._usedPort = 0
        ADDON.setSetting('notify_server_port', str(self._usedPort))

    def closeServer(self):
        self._stop = True
        s = None
        #fake a notify to stop the thread
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, self._usedPort))
            s.sendall('')
        except socket.error as e:
            log_error("NotifySyncServer EXCEPTION : %s" %(repr(e)) )
        finally:
            if s:
                s.close()
        #wait for the thread
        self.join()
        
    def getNotification(self):
        '''
        returns one notification per call
        '''
        account_name = None
        notification = None
        if not self._notifyList.empty():
            try:
                data = json.loads( self._notifyList.get() )
                account_name = data[0]
                notification = data[1]
            except Exception as e:
                log_error('NotifySyncServer: failed to parse recieved data!')
        return account_name, notification

    def run(self):
        self.setupServer()
        log_debug('NotifySyncServer started')
        while(not self._stop and self._socket):
            clientsocket = None
            #Check for new client connection
            try:
                (clientsocket, address) = self._socket.accept()
            except socket.timeout as e:
                log_debug("NotifySyncServer exception : %s" %(repr(e)) )
            except socket.error as e:
                log_error("NotifySyncServer EXCEPTION : %s" %(repr(e)) )
            except:
                log_error("NotifySyncServer EXCEPTION!")
            if clientsocket:
                #Check the socket for new notificatios from client(s))
                data = clientsocket.recv(SOCKET_BUFFER_SIZE)
                log_debug("NotifySyncServer received data: %s" %(repr(data)) )
                self._notifyList.put(data)
                clientsocket.close()
        if self._socket:
            self._socket.close()
            self._socket = None
        log_debug('NotifySyncServer stopped')

class NotifySyncClient(object):
    '''
    NotifySyncClient is the client of NotifySyncServer and reports an event to
    NotifySyncServer by sending data over the TCP socket.
    '''
    def send_notification(self, account_name, notification, data=None):
        s = None
        usedPort = int( ADDON.getSetting('notify_server_port') )
        if usedPort > 0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, usedPort))
                send_data = json.dumps([account_name, notification, data])
                s.sendall(send_data)
                log_debug('NotifySyncClient send: %s' %(repr(send_data)))
            except socket.error as e:
                log_error("NotifySyncClient EXCEPTION : %s" %(repr(e)) )
            finally:
                if s:
                    s.close()
        else:
            log_error('NotifySyncClient no port defined')
    
    def sync_path(self, account, path):
        # check if synchronization n enabled and check if the path is somewhere
        # in the remote path
        if account.synchronisation and (account.remotepath in path):
            #ignore the path for now! Otherwise need to change receiving number of
            # SOCKET_BUFFER_SIZE according to the path string size!
            self.send_notification(account.account_name, NOTIFY_SYNC_PATH)
        else:
            log_debug('NotifySyncClient Sync not enabled or path not part of remote sync path')

    def account_settings_changed(self, account):
        self.send_notification(account.account_name, NOTIFY_CHANGED_ACCOUNT)

    def account_added_removed(self):
        self.send_notification(None, NOTIFY_ADDED_REMOVED_ACCOUNT)