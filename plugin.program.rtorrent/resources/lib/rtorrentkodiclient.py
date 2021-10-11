''' Wrapper around xmlrpc with Kodi-specific behaviour '''
import os
import sys
import xmlrpc.client
from urllib.parse import urlparse
import xbmc
import xbmcgui
from . import rtorrent_xmlrpc
from . import globals as g

class RTorrentKodiClient:
    ''' Wrapper around xmlrpc calls '''
    def __init__(self):
        self.success = True
        self.make_connection()
    def make_connection(self):
        ''' Creates (and updates) the connection string from settings '''
        self.uri = urlparse(g.__setting__('uri'))
        if self.uri.scheme == 'scgi':
            self.connection = rtorrent_xmlrpc.SCGIServerProxy(self.uri.geturl())
        else:
            self.connection = xmlrpc.client.ServerProxy(self.uri.geturl())
    def call(self, method, *params):
        ''' Makes the XMLRPC call and excessively catches and handles errors '''
        attempts = 10
        for attempt in range(attempts):
            if attempt == attempts-1:
                raise 'Connection attempts exhausted!'
            try:
                self.success = True
                result = getattr(self.connection, method)(*params)
                break
            except xmlrpc.client.ProtocolError as err:
                self.success = False
                error_dialog(g.__lang__(30906), False)
                xbmc.log("An XMLRPC protocol error occurred")
                xbmc.log("URL: %s" % err.url)
                xbmc.log("HTTP/HTTPS headers: %s" % err.headers)
                xbmc.log("Error code: %d" % err.errcode)
                xbmc.log("Error message: %s" % err.errmsg)
                raise
            except xmlrpc.client.Fault as err:
                self.success = False
                error_dialog(g.__lang__(30907), False)
                xbmc.log("An XMLRPC fault occurred")
                xbmc.log("Fault code: %d" % err.faultCode)
                xbmc.log("Fault string: %s" % err.faultString)
                raise
            except ConnectionRefusedError:
                self.success = False
                if not error_dialog(g.__lang__(30908)):
                    raise
                self.make_connection()
            except TimeoutError:
                self.success = False
                if not error_dialog(g.__lang__(30909)):
                    raise
                self.make_connection()
            except:
                self.success = False
                xbmc.log("Unexpected error:", sys.exc_info()[0])
                error_dialog(g.__lang__(30910), False)
                raise
        return result
    def local(self):
        ''' Work out if rTorrent is running on the same machine. '''
        local_names = ['localhost', '127.0.0.1', os.getenv('COMPUTERNAME'), None]
        if self.uri.hostname in local_names:
            return True
        return False

def error_dialog(message, show_settings=True):
    ''' Display error dialog '''
    if show_settings:
        dialog = xbmcgui.Dialog().yesno(
            g.__lang__(30902),
            message,
            g.__lang__(30904),
            g.__lang__(30903),
        )
        if dialog:
            g.__addon__.openSettings()
            return True
    else:
        xbmcgui.Dialog().ok(
            g.__lang__(30902),
            message,
        )
    return False
