# -*- coding: utf-8 -*-
import xbmc
import sys
import re


class RTMP:
    def __init__(self, rtmp, tcUrl = None, auth = None, app = None, playPath = None, swfUrl = None, swfVfy = None, pageUrl = None, live = None, socks = None, port = None):
        if hasattr(sys.modules[u"__main__"], u"log"):
            self.log = sys.modules[u"__main__"].log
        else:
            from utils import log
        
        self.rtmp = rtmp
        self.tcUrl = tcUrl
        self.auth = auth
        self.app = app
        self.playPath = playPath
        self.swfUrl = swfUrl
        self.swfVfy = swfVfy
        self.pageUrl = pageUrl
        self.live = live
        self.socks = socks
        self.port = port
        
        self.rtmpdumpPath = None
        self.downloadFolder = None

        self.language = sys.modules["__main__"].language
    
    # hostname:port
    def setProxyString(self, string):
        self.socks = string
        
    def setDownloadDetails(self, rtmpdumpPath, downloadFolder):
        self.rtmpdumpPath = rtmpdumpPath
        self.downloadFolder = downloadFolder
        
        self.log (u"setDownloadDetails rtmpdumpPath: %s, downloadFolder: %s" % (self.rtmpdumpPath, self.downloadFolder), xbmc.LOGDEBUG)


    def getDumpCommand(self):
        if self.rtmpdumpPath is None or self.rtmpdumpPath == '':
            # rtmpdump path is not set
            exception = Exception(self.language(30042))
            raise exception

        args = [ self.rtmpdumpPath ]

        args.append(getParameters())

        command = ' '.join(args)

        self.log(u"command: " + command, xbmc.LOGDEBUG)
        return command

    def getSimpleParameters(self):
        if self.downloadFolder is None or self.downloadFolder == '':
            # Download Folder is not set
            exception = Exception(self.language(30043))
            raise exception;

        if self.rtmp is None or self.rtmp == '':
            # rtmp url is not set
            exception = Exception(self.language(30044))
            raise exception;

        parameters = {}

        parameters[u"url"] = self.rtmp
        parameters[u"download_path"] = self.downloadFolder

        if self.auth is not None:
            parameters[u"auth"] = self.auth

        if self.app is not None:
            parameters[u"app"] = self.app

        if self.playPath is not None:
            parameters[u"playpath"] = self.playPath

        if self.tcUrl is not None:
            parameters[u"tcUrl"] = self.tcUrl

        if self.swfUrl is not None:
            parameters[u"swfUrl"] = self.swfUrl

        if self.swfVfy is not None:
            parameters[u"swfVfy"] = self.swfVfy

        if self.pageUrl is not None:
            parameters[u"pageUrl"] = self.pageUrl

        if self.live is not None and self.live is not False:
            parameters[u"live"] = u"true"

        if self.socks is not None:
            parameters[u"socks"] = self.socks

        if self.port is not None:
            parameters[u"port"] = self.port

        self.log(u"parameters: " + unicode(parameters), xbmc.LOGDEBUG)
        return parameters

    def getParameters(self):
        if self.downloadFolder is None or self.downloadFolder == '':
            # Download Folder is not set
            exception = Exception(self.language(30043))
            raise exception;

        if self.rtmp is None or self.rtmp == '':
            # rtmp url is not set
            exception = Exception(self.language(30044))
            raise exception;

        args = [ u"--rtmp", u'"%s"' % self.rtmp, u"-o", u'"%s"' % self.downloadFolder ]

        if self.auth is not None:
            args.append(u"--auth")
            args.append(u'"%s"' % self.auth)

        if self.app is not None:
            args.append(u"--app")
            args.append(u'"%s"' % self.app)

        if self.playPath is not None:
            args.append(u"--playpath")
            args.append(u'"%s"' % self.playPath)

        if self.swfUrl is not None:
            args.append(u"--swfUrl")
            args.append(u'"%s"' % self.swfUrl)

        if self.tcUrl is not None:
            args.append(u"--tcUrl")
            args.append(u'"%s"' % self.tcUrl)

        if self.swfVfy is not None:
            args.append(u"--swfVfy")
            args.append(u'"%s"' % self.swfVfy)

        if self.pageUrl is not None:
            args.append(u"--pageUrl")
            args.append(u'"%s"' % self.pageUrl)

        if self.live is not None and self.live is not False:
            args.append(u"--live")

        if self.socks is not None:
            args.append(u"--socks")
            args.append(u'"%s"' % self.socks)

        if self.port is not None:
            args.append(u"--port")
            args.append(u'%d' % self.port)
            
        parameters = u' '.join(args)

        self.log(u"parameters: " + parameters, xbmc.LOGDEBUG)
        return parameters

    def getPlayUrl(self):
        if self.rtmp is None or self.rtmp == '':
            # rtmp url is not set
            exception = Exception(self.language(30044))
            raise exception;

        if self.port is None:
            args = [u"%s" % self.rtmp]
        else:
            try:
                # Replace "rtmp://abc.def.com:default_port/ghi/jkl" with "rtmp://abc.def.com:port/ghi/jkl"
                match=re.search("(.+//[^/]+):\d+(/.*)", self.rtmp,  re.DOTALL | re.IGNORECASE )
                if match is None:
                    # Replace "rtmp://abc.def.com/ghi/jkl" with "rtmp://abc.def.com:port/ghi/jkl"
                    match=re.search("(.+//[^/]+)(/.*)", self.rtmp,  re.DOTALL | re.IGNORECASE )
                    
                args = [u"%s:%d%s" % (match.group(1), self.port, match.group(2))]
            except (Exception) as exception:
                self.log("Exception changing default port: " + repr(exception))
                args = [u"%s" % self.rtmp]

        if self.auth is not None:
            args.append(u"auth=%s" % self.auth)

        if self.app is not None:
            args.append(u"app=%s" % self.app)

        if self.playPath is not None:
            args.append(u"playpath=%s" % self.playPath)

        if self.swfUrl is not None:
            args.append(u"swfurl=%s" % self.swfUrl)

        if self.tcUrl is not None:
            args.append(u"tcUrl=%s" % self.tcUrl)

        if self.swfVfy is not None:
            args.append(u"swfurl=%s" % self.swfVfy)
            args.append(u"swfvfy=true")

        if self.pageUrl is not None:
            args.append(u"pageurl=%s" % self.pageUrl)

        if self.live is not None and self.live is not False:
            args.append(u"live=true")

        if self.socks is not None:
            args.append(u"socks=%s" % self.socks)

        playURL = u' '.join(args)

        self.log(u"playURL: " + playURL, xbmc.LOGDEBUG)

        return playURL


