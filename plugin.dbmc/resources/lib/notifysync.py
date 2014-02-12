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

from resources.lib.utils import *

HOST = '127.0.0.1' #use 127.0.0.1 needed for windows
PORT = 0 #Let OS get a free port
SOCKET_BUFFER_SIZE = 1024

class NotifySyncServer(threading.Thread):
    
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
        data = []
        while not self._notifyList.empty():
            data.append( self._notifyList.get() )
        return data

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
    
    def notify(self, path):
        s = None
        usedPort = int( ADDON.getSetting('notify_server_port') )
        syncEnabled = ('true' == ADDON.getSetting('synchronisation').lower())
        if syncEnabled and usedPort > 0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, usedPort))
                s.sendall(path)
                log_debug('NotifySyncClient send: %s' %(repr(path)))
            except socket.error as e:
                log_error("NotifySyncClient EXCEPTION : %s" %(repr(e)) )
            finally:
                if s:
                    s.close()
        else:
            log_debug('NotifySyncClient Sync not enabled or no port defined')
