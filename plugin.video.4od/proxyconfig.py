import sys

import urllib2
import httplib
import socks

class ProxyConfig:
    def __init__(self, type, server, port, dns = True, user = None, password = None):
        self.server = server
        self.type = type
        self.port = port
        self.user = user
        self.password = password
        self.dns = dns
        self.urllib2_socket = None
        self.httplib_socket = None
                
    #==============================================================================
    
    def Enable(self):
        self.urllib2_socket = None
        self.httplib_socket = None
        
        log = sys.modules[u"__main__"].log
        
        try:
            log(u"Using proxy: type %i rdns: %i server: %s port: %s user: %s pass: %s" % (self.type, self.dns, self.server, self.port, u"***", u"***") )
    
            self.urllib2_socket = urllib2.socket.socket 
            self.httplib_socket = httplib.socket.socket
             
            socks.setdefaultproxy(self.type, self.server, self.port, self.dns, self.user, self.password)
            socks.wrapmodule(urllib2)
            socks.wrapmodule(httplib)
        except ( Exception ) as exception:
            log(u"Error processing proxy settings", xbmc.LOGERROR)
            log(u"Exception: " + exception.me, xbmc.LOGERROR)
            
    def Disable(self):
        
        if self.urllib2_socket is not None:
            urllib2.socket.socket = self.urllib2_socket
            
        if self.httplib_socket is not None:
            httplib.socket.socket = self.httplib_socket
             
        self.urllib2_socket = None
        self.httplib_socket = None
        

    def toString(self):
        #string = ""
        #if self.user is not None and self.password is not None:
        #    string = "%s:%s@" % (self.user, self.password)
        
        #string = string + "%s:%s" % (self.server, self.port)
        string = u"%s:%s" % (self.server, self.port)
        
        return string