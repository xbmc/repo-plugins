import socket
import threading
import SocketServer
import xbmc
import xbmcaddon
from resources.lib.api.OneDriveHTTPRequestHandler import OneDriveHTTPRequestHandler

addon = xbmcaddon.Addon()
interface = '127.0.0.1'
def unused_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((interface, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

service_port = unused_port()
addon.setSetting('http.service.port', str(service_port))
xbmc.log('OneDrive http service port: ' + str(service_port), xbmc.LOGNOTICE)
SocketServer.TCPServer.allow_reuse_address = True
server = SocketServer.TCPServer((interface, service_port), OneDriveHTTPRequestHandler)
server.server_activate()
server.timeout = 1

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    while not monitor.abortRequested():
        if monitor.waitForAbort(3):
            server.shutdown()
            break
    server.server_close()
    server.socket.close()
    server.shutdown()
    xbmc.log('OneDrive http service stopped', xbmc.LOGNOTICE)
    
    