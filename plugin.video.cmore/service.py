# Author: asciidisco
# Module: service
# Created on: 13.01.2017
# License: MIT https://goo.gl/5bMj3H

import threading
import SocketServer
import socket
from xbmc import Monitor
from resources.lib.kodihelper import KodiHelper
from resources.lib.WidevineHTTPRequestHandler import WidevineHTTPRequestHandler

# helper function to select an unused port on the host machine
def select_unused_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    addr, port = sock.getsockname()
    sock.close()
    return port

helper = KodiHelper()

# pick & store a port for the proxy service
wv_proxy_port = select_unused_port()
helper.set_setting('wv_proxy_port', str(wv_proxy_port))
helper.log('Port {0} selected'.format(str(wv_proxy_port)))

# server defaults
SocketServer.TCPServer.allow_reuse_address = True
# configure the proxy server
wv_proxy = SocketServer.TCPServer(('127.0.0.1', wv_proxy_port), WidevineHTTPRequestHandler)
wv_proxy.server_activate()
wv_proxy.timeout = 1

if __name__ == '__main__':
    monitor = Monitor()
    # start thread for proxy server
    proxy_thread = threading.Thread(target=wv_proxy.serve_forever)
    proxy_thread.daemon = True
    proxy_thread.start()

    # kill the services if kodi monitor tells us to
    while not monitor.abortRequested():
        if monitor.waitForAbort(5):
            wv_proxy.shutdown()
            break

    # wv-proxy service shutdown sequence
    wv_proxy.server_close()
    wv_proxy.socket.close()
    wv_proxy.shutdown()
    helper.log('wv-proxy stopped')
