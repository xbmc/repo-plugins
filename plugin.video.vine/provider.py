# -*- coding: utf-8 -*-
import os
import sys
import re
import random
import socks
import proxyconfig
import unicodedata

from loggingexception import LoggingException
from urlparse import urlunparse
import HTMLParser

from rtmp import RTMP

if hasattr(sys.modules["__main__"], "xbmc"):
    xbmc = sys.modules["__main__"].xbmc
else:
    import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
    xbmcgui = sys.modules["__main__"].xbmcgui
else:
    import xbmcgui

from subprocess import Popen, PIPE, STDOUT
import mycgi
import utils

countryInfoUrl = "http://api.hostip.info/country.php"

class Provider(object):

    def __init__(self):
        self.proxy = None
        self.useBitRateSetting = False
        if hasattr(sys.modules["__main__"], "log"):
            self.log = sys.modules["__main__"].log
        else:
            from utils import log
            self.log = log

            self.log("")

        self.player = xbmc.Player

    def SetPlayer(self, player):
        self.player = player

    def CreateForwardedForIP(self, currentForwardedForIP):
        currentSegments = currentForwardedForIP.split('.')
        
        ipSegment1 = int(float(self.addon.getSetting(u'forward_segment1')))
        ipSegment2 = int(float(self.addon.getSetting(u'forward_segment2')))

        if len(currentSegments) == 4 and int(currentSegments[0]) == ipSegment1 and int(currentSegments[1]) == ipSegment2:
            # Settings haven't changed, return the current ip
            return currentForwardedForIP
        
        forwardedForIP = '%d.%d.%d.%d' % (ipSegment1, ipSegment2, random.randint(0, 255), random.randint(0, 254)) 
 
        return forwardedForIP 

    """
    If there is exactly one parameter then we are showing a provider's root menu
    otherwise we need to look at the other parameters to see what we need to do
    """
    def ExecuteCommand(self, mycgi):
        self.log(u"mycgi.ParamCount(): " + unicode(mycgi.ParamCount()), xbmc.LOGDEBUG)
        forwardedIP = mycgi.Param( u'forwardedip' )
        
        if self.httpManager.GetIsForwardedForIP():
             forwardedIP = self.CreateForwardedForIP(forwardedIP)
             
        if forwardedIP <> u'':
            self.httpManager.SetForwardedForIP( forwardedIP )
 
        if mycgi.ParamCount() > 1:
            return self.ParseCommand(mycgi)
            ##return True
        else:
            #self.ShowLocationInfo()
            return self.ShowRootMenu()
    
    def ShowLocationInfo(self):
        try:
            html = None
            html = self.httpManager.GetWebPageDirect(countryInfoUrl)
    
            self.log(u"Country code: " + html)
        except (Exception) as exception:
            self.log(u"Exception getting country code: " + repr(exception))
            
            
    def initialise(self, httpManager, baseurl, pluginhandle):
        self.baseurl = baseurl
        self.pluginhandle = pluginhandle
        self.addon = sys.modules[u"__main__"].addon
        self.language = sys.modules[u"__main__"].language
        
        self.METHOD_IP_FORWARD = self.language(30370) 
        self.METHOD_PROXY = self.language(31010)
        self.METHOD_PROXY_STREAMS = self.language(31020)
        
        
        self.InitialiseHTTP(httpManager)
        
    def GetProxyConfig(self):

        proxy_server = None
        proxy_type_id = 0
        proxy_port = 8080
        proxy_user = None
        proxy_pass = None
        try:
            proxy_server = self.addon.getSetting(u'proxy_server')
            proxy_type_id = self.addon.getSetting(u'proxy_type')
            proxy_port = int(self.addon.getSetting(u'proxy_port'))
            proxy_user = self.addon.getSetting(u'proxy_user')
            proxy_pass = self.addon.getSetting(u'proxy_pass')
        except ( Exception ) as exception:
            raise exception
    
        if   proxy_type_id == u'0': proxy_type = socks.PROXY_TYPE_HTTP_NO_TUNNEL
        elif proxy_type_id == u'1': proxy_type = socks.PROXY_TYPE_HTTP
        elif proxy_type_id == u'2': proxy_type = socks.PROXY_TYPE_SOCKS4
        elif proxy_type_id == u'3': proxy_type = socks.PROXY_TYPE_SOCKS5
    
        proxy_dns = True
    
        if proxy_user == u'':
            proxy_user = None
    
        if proxy_pass == u'':
            proxy_pass = None

        proxyConfig = proxyconfig.ProxyConfig( proxy_type, proxy_server, proxy_port, proxy_dns, proxy_user, proxy_pass)
        
        return proxyConfig
    
        
    def InitialiseHTTP(self, httpManager):
        self.httpManager = httpManager
        self.httpManager.SetDefaultHeaders( self.GetHeaders() )

        proxy_method = self.addon.getSetting(self.GetProviderId() + u'_proxy_method') 
        self.log("proxy_method: %s" % proxy_method)
        
        if proxy_method == self.METHOD_PROXY or proxy_method == self.METHOD_PROXY_STREAMS:
            proxyConfig = self.GetProxyConfig()
            self.httpManager.SetProxyConfig( proxyConfig )
        elif proxy_method == self.METHOD_IP_FORWARD:
            self.httpManager.EnableForwardedForIP()

    def GetBitRateSetting(self):
        if self.useBitRateSetting is False:
            return None
        
        bitRates = {
            u"":None,                            #Setting not set, so use default value
            self.language(32400):None,           #Default
            self.language(32410):-1,             #Lowest Available
            self.language(32430):200 * 1024,     #Max 200kps
            self.language(32440):350 * 1024,     #Max 350kps
            self.language(32450):500 * 1024,     #Max 500kps
            self.language(32460):750 * 1024,     #Max 750kps
            self.language(32470):1000 * 1024,    #Max 1000kps
            self.language(32480):1500 * 1024,    #Max 1500kps
            self.language(32490):2000 * 1024,    #Max 2000kps
            self.language(32420):20000 * 1024    #Highest Available
            }

        bitrate_string = self.addon.getSetting(u'bitrate')
        
        return bitRates[bitrate_string]


    def GetURLStart(self):
        urlStart = self.baseurl + u'?provider=' + self.GetProviderId() 
        forwardedIP = self.httpManager.GetForwardedForIP()
        if forwardedIP is not None:
            urlStart = urlStart + u'&forwardedip=' + forwardedIP
             
        return urlStart
    
    def GetHeaders(self):
        # Windows 8, Internet Explorer 10
        headers = {
                   'User-Agent' : "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)",
                   'DNT' : '1'
                   }
        return headers

    def GetProviderId(self):
        pass
    
    def ShowRootMenu(self):
        pass
    
    def ParseCommand(self, mycgi):
        pass

    def GetRootContextMenuItems(self):
        return None

    def GetAction(self, title):
        actionSetting = self.addon.getSetting( u'select_action' ).decode('utf8')
        self.log (u"action: " + actionSetting, xbmc.LOGDEBUG)
    
        # Ask
        if ( actionSetting == self.language(30120) ):
            dialog = xbmcgui.Dialog()
            # Do you want to play or download?    
    
            action = dialog.yesno(title, self.language(30530), u'', u'', self.language(30140),  self.language(30130)) # 1=Play; 0=Download
        # Download
        elif ( actionSetting == self.language(30140) ):
            action = 0
        else:
            action = 1
    
        return action
    
    #==============================================================================
    def AddSocksToRTMP(self, rtmpVar):
        stream_method = self.addon.getSetting(self.GetProviderId() + u'_proxy_method') 
        if stream_method == self.METHOD_PROXY_STREAMS:
            proxyConfig = self.GetProxyConfig()
            rtmpVar.setProxyString(proxyConfig.toString())
        
    def PlayOrDownloadEpisode(self, infoLabels, thumbnail, rtmpVar = None, defaultFilename = '', url = None, subtitles = None):
        try:
            action = self.GetAction(infoLabels['Title'])
    
            if self.dialog.iscanceled():
                return False
            
            if ( action == 1 ):
                # Play
                # "Preparing to play video"
                self.dialog.update(50, self.language(32720))
                self.Play(infoLabels, thumbnail, rtmpVar, url, subtitles)
        
            elif ( action == 0 ):
                    # Download
                    # "Preparing to download video"
                self.dialog.update(50, self.language(32730))
                self.Download(rtmpVar, defaultFilename, subtitles)
    
            return True
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            # Error playing or downloading episode %s
            exception.process(self.language(32120) % u'', u'', self.logLevel(xbmc.LOGERROR))
            return False
    
    def GetPlayer(self):
        return xbmc.Player(xbmc.PLAYER_CORE_AUTO) 
    
    def Play(self, infoLabels, thumbnail, rtmpVar = None, url = None, subtitles = None):
        if infoLabels is None:
            self.log (u'Play titleId: Unknown Title')
            listItem = xbmcgui.ListItem(u'Unknown Title')
        else:
            self.log (u'Play titleId: ' + infoLabels[u'Title'])
            listItem = xbmcgui.ListItem(infoLabels[u'Title'])
            listItem.setInfo(u'video', infoLabels)

        if thumbnail is not None:
            listItem.setThumbnailImage(thumbnail)
    
        playList=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playList.clear()
        
        if url is None:
            url = rtmpVar.getPlayUrl()
            
        playList.add(url, listItem)
    
        if self.dialog.iscanceled():
            return False
        
        player = self.GetPlayer()
        player.play(playList)
        
        self.dialog.close()
        
        if subtitles is not None:
            try:
                subtitleFile = subtitles.GetSubtitleFile()
                self.player().setSubtitles(subtitleFile)
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
            
                # Error getting subtitles
                exception.addLogMessage(self.language(30970))
                exception.process('', '', severity = xbmc.LOGWARNING)

        # Keep script alive so that player can process the onPlayBackStart event
        if player.isPlaying():
            xbmc.sleep(5000)

    def Download(self, rtmpVar, defaultFilename, subtitles = None):
        (rtmpdumpPath, downloadFolder, filename) = self.GetDownloadSettings(defaultFilename)
    
        savePath = os.path.join( downloadFolder, filename )
        rtmpVar.setDownloadDetails(rtmpdumpPath, savePath)
        parameters = rtmpVar.getParameters()

        if subtitles is not None:
            self.log (u"Getting subtitles")

        if subtitles is not None:
            try:
                # Replace '.flv' or other 3 character extension with '.smi'
                subtitleFile = subtitles.GetSubtitleFile(savePath[0:-4] + u'.smi')
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
            
                # Error getting subtitles
                exception.addLogMessage(self.language(30970))
                exception.process('', '', severity = xbmc.LOGWARNING)

        # Starting downloads 
        self.log (u"Starting download: " + rtmpdumpPath + u" " + parameters)
    
        xbmc.executebuiltin(('XBMC.Notification(%s, %s)' % ( self.language(30610), filename)).encode('utf8'))
    
        self.log(u'"%s" %s' % (rtmpdumpPath, parameters))
        if sys.modules[u"__main__"].get_system_platform() == u'windows':
            p = Popen( parameters, executable=rtmpdumpPath, shell=True, stdout=PIPE, stderr=PIPE )
        else:
            cmdline = u'"%s" %s' % (rtmpdumpPath, parameters)
            p = Popen( cmdline, shell=True, stdout=PIPE, stderr=PIPE )
    
        self.log (u"rtmpdump has started executing", xbmc.LOGDEBUG)
        (stdout, stderr) = p.communicate()
        self.log (u"rtmpdump has stopped executing", xbmc.LOGDEBUG)
    
        if u'Download complete' in stderr:
            # Download Finished!
            self.log (u'stdout: ' + str(stdout), xbmc.LOGDEBUG)
            self.log (u'stderr: ' + str(stderr), xbmc.LOGDEBUG)
            self.log (u"Download Finished!")
            xbmc.executebuiltin(('XBMC.Notification(%s,%s,2000)' % ( self.language(30620), filename)).encode('utf8'))
        else:
            # Download Failed!
            self.log (u'stdout: ' + str(stdout), xbmc.LOGERROR)
            self.log (u'stderr: ' + str(stderr), xbmc.LOGERROR)
            self.log (u"Download Failed!")
            xbmc.executebuiltin(('XBMC.Notification(%s,%s,2000)' % ( u"Download Failed! See log for details", filename)).encode('utf8'))

    #==============================================================================
    
    def GetDownloadSettings(self, defaultFilename):
    
        # Ensure rtmpdump has been located
        rtmpdumpPath = self.addon.getSetting(u'rtmpdump_path').decode('utf8')
        if ( rtmpdumpPath is u'' ):
            dialog = xbmcgui.Dialog()
            # Download Error - You have not located your rtmpdump executable...
            dialog.ok(self.language(30560),self.language(30570),u'',u'')
            self.addon.openSettings(sys.argv[ 0 ])
            
            rtmpdumpPath = self.addon.getSetting(u'rtmpdump_path').decode('utf8')

        if ( rtmpdumpPath is u'' ):
            return
        
        # Ensure default download folder is defined
        downloadFolder = self.addon.getSetting(u'download_folder').decode('utf8')
        if downloadFolder is '':
            d = xbmcgui.Dialog()
            # Download Error - You have not set the default download folder.\n Please update the self.addon settings and try again.','','')
            d.ok(self.language(30560),self.language(30580),u'',u'')
            self.addon.openSettings(sys.argv[ 0 ])
            
            downloadFolder = self.addon.getSetting(u'download_folder').decode('utf8')

        if downloadFolder is '':
            return
        
        if ( self.addon.getSetting(u'ask_filename') == u'true' ):
            # Save programme as...
            kb = xbmc.Keyboard( defaultFilename, self.language(30590))
            kb.doModal()
            if (kb.isConfirmed()):
                filename = kb.getText().decode('utf8')
            else:
                return
        else:
            filename = defaultFilename
        
        if ( filename.endswith(u'.flv') == False ): 
            filename = filename + u'.flv'
        
        if ( self.addon.getSetting(u'ask_folder') == u'true' ):
            dialog = xbmcgui.Dialog()
            # Save to folder...
            downloadFolder = dialog.browse(  3, self.language(30600), u'files', u'', False, False, downloadFolder ).decode('utf8')

        if ( downloadFolder == u'' ):
            return
        
        return (rtmpdumpPath, downloadFolder, filename)

    def logLevel(self, requestLevel):
        if self.lastPageFromCache():
            return xbmc.LOGDEBUG
        
        return requestLevel
    
    def lastPageFromCache(self):
        if self.httpManager.getGotFromCache() and self.httpManager.getGotFromCache():
            return True
        
        return False
    
    #==============================================================================
    # thumbnail must be unicode, not str
    def GetThumbnailPath(self, thumbnail):
        thumbnail = unicodedata.normalize('NFKD', thumbnail).encode('ASCII', 'ignore')
        thumbnail = utils.replace_non_alphanum(thumbnail)
        self.log("thumbnail: " + thumbnail, xbmc.LOGDEBUG)
        path = os.path.join(sys.modules[u"__main__"].MEDIA_PATH, self.GetProviderId() + '_' + thumbnail + '.jpg')
        
        if not os.path.exists(path):
            path = os.path.join(sys.modules[u"__main__"].MEDIA_PATH, self.GetProviderId() + '.jpg') 

        if self.log is not None:
            self.log("GetThumbnailPath: " + path, xbmc.LOGDEBUG)
        return path
    #
    def fullDecode(self, text):
        htmlparser = HTMLParser.HTMLParser()
        text = text.replace(u'&#39;', u"'" )
        text = htmlparser.unescape(text)

        mychr = chr
        myatoi = int
        list = text.split('%')
        res = [list[0]]
        myappend = res.append
        del list[0]
        for item in list:
            if item[1:2]:
                try:
                    myappend(unicode(chr(int(item[:2], 16)), 'latin1') + item[2:])
                except:
                    myappend('%' + item)
            else:
                myappend('%' + item)
        return u"".join(res)
                 
#==============================================================================
    def DoSearch(self):
        self.log("", xbmc.LOGDEBUG)
        # Search
        kb = xbmc.Keyboard( "", self.language(30500) )
        kb.doModal()
        if ( kb.isConfirmed() == False ): return
        query = kb.getText()

        return self.DoSearchQuery( query = query )

    # Download the given url and return the first string that matches the pattern
    def GetStringFromURL(self, url, pattern, maxAge = 20000):
        self.log(u"url '%s', pattern '%s'" % (url, pattern), xbmc.LOGDEBUG)
    
        try:
            data = None
            data = self.httpManager.GetWebPage(url, maxAge)
    
            self.log(u"len(data): " + str(len(data)), xbmc.LOGDEBUG)
    
            return re.search(pattern, data).groups()
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)
    
            if data is not None:
                msg = "url: %s\n\n%s\n\n" % (url, data)
                exception.addLogMessage(msg)
                
            # Error getting web page %s
            exception.addLogMessage(self.language(30050) + ": " + url)
            raise exception
    
    def PlayVideoWithDialog(self, method, parameters):
        try:
            self.dialog = xbmcgui.DialogProgress()
            self.dialog.create(self.GetProviderId(), self.language(32640))
            
            return method(*parameters)
        finally:
            self.dialog.close()


class Subtitle(object):
    
    def GetSubtitleFile(self, filename = None):
        return sys.modules[u"__main__"].NO_SUBTITLE_FILE
