'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

import socket
import threading
import SocketServer
import xbmc
import xbmcaddon
from resources.lib.api.download import download
from resources.lib.api.source import source

addon = xbmcaddon.Addon()
interface = '127.0.0.1'
dirlist_allow = addon.getSetting('allow_directory_listing') == 'true'

def unused_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((interface, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

service_port = unused_port()
addon.setSetting('http.service.port', str(service_port))
xbmc.log('OneDrive Download service port: ' + str(service_port), xbmc.LOGNOTICE)

SocketServer.TCPServer.allow_reuse_address = True

service_server = SocketServer.TCPServer((interface, service_port), download)
service_server.server_activate()
service_server.timeout = 1


if dirlist_allow:
    dirlist_port = int(addon.getSetting('port_directory_listing'))
    dirlist_server = SocketServer.TCPServer((interface, dirlist_port), source)
    dirlist_server.server_activate()
    dirlist_server.timeout = 1

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    service_thread = threading.Thread(target=service_server.serve_forever)
    service_thread.daemon = True
    service_thread.start()

    if dirlist_allow:
        dirlist_thread = threading.Thread(target=dirlist_server.serve_forever)
        dirlist_thread.daemon = True
        dirlist_thread.start()
        xbmc.log('OneDrive Directory Listing started in port ' + str(dirlist_port), xbmc.LOGNOTICE)
    
    while not monitor.abortRequested():
        if monitor.waitForAbort(3):
            service_server.shutdown()
            if dirlist_allow:
                dirlist_server.shutdown()
            break
    
    service_server.server_close()
    service_server.socket.close()
    service_server.shutdown()
    
    if dirlist_allow:
        dirlist_server.server_close()
        dirlist_server.socket.close()
        dirlist_server.shutdown()
    
    xbmc.log('OneDrive services stopped', xbmc.LOGNOTICE)
    
    