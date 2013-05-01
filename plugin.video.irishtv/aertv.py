# -*- coding: utf-8 -*-
import re
import sys
from time import strftime, strptime
import time, random
import simplejson

from datetime import datetime, timedelta

from urlparse import urljoin

if hasattr(sys.modules["__main__"], "xbmc"):
    xbmc = sys.modules["__main__"].xbmc
else:
    import xbmc
    
if hasattr(sys.modules["__main__"], "xbmcgui"):
    xbmcgui = sys.modules["__main__"].xbmcgui
else:
    import xbmcgui

if hasattr(sys.modules["__main__"], "xbmcplugin"):
    xbmcplugin = sys.modules["__main__"].xbmcplugin
else:
    import xbmcplugin

import mycgi
import utils
from loggingexception import LoggingException
import rtmp

import HTMLParser
from BeautifulSoup import BeautifulSoup

from provider import Provider
from brightcove import BrightCoveProvider

urlRoot     = u"http://www.aertv.ie"
apiRoot     = u"http://api.aertv.ie"
c_brightcove = u"http://c.brightcove.com"

# Default values only used if we can't get the info from the net, e.g. only used if we can't get the info from the net
defaultRTMPUrl = u"rtmpe://85.91.5.163:1935/rtplive&" 

TIME_FORMAT = u"%Y-%m-%dT%H:%M:%S"

# RTMP stub 
channelToStream = {
                u'rte-one' : u'RTEONE_v500.stream',
                u'rte-two' : u'RTETWO_v500.stream',
                u'rte-two-hd' : u'RTETWOHD_v1500.stream',
                u'tv3' : u'TV3_v500.stream',
                u'tg4' : u'TG4_v500.stream',
                u'3e' : u'3E_v500.stream',
                u'rte-one1' : u'RTEPLUSONE_v500.stream',
                u'rte-news-now' : u'RTENEWSNOW_v500.stream',
                u'rtejr' : u'RTEJUNIOR_v500.stream'
                }

class AerTVProvider(BrightCoveProvider):

    def __init__(self):
        super(AerTVProvider, self).__init__()

    def GetProviderId(self):
        return u"AerTV"

    def ExecuteCommand(self, mycgi):
        return super(AerTVProvider, self).ExecuteCommand(mycgi)

    def GetJSONPath(self):
        epochTimeMS = int(round(time.time() * 1000.0))
        # POST ?callback=jQuery18208056761118918062_1358250191844 HTTP/1.1
        callbackToken = "?callback=jQuery1820%s_%s" % ( random.randint(3000000, 90000000000), epochTimeMS)
        return callbackToken 

    def ShowRootMenu(self):
        self.log(u"", xbmc.LOGDEBUG)
        
        try:
            ddlJSONText = None
            epgJSON = None 
            values = {'api':'ddl', 'type':'basic'}
            url = self.GetAPIUrl(values)

            ddlJSONText = self.httpManager.GetWebPage(url, 7200)
            ddlJSONText = utils.extractJSON(ddlJSONText)
            ddlJSON = simplejson.loads(ddlJSONText)
            
            values = {'api':'epg', 'type':'basic'}
            url = self.GetAPIUrl(values)
            epgJSON = self.GetEpgJSON(url)

            return self.ShowChannelList(url, ddlJSON, epgJSON)
        
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if ddlJSONText is not None:
                msg = "ddlJSONText:\n\n%s\n\n" % ddlJSONText
                exception.addLogMessage(msg)
            
            if epgJSON is not None:
                msg = "epgJSON:\n\n%s\n\n" % utils.drepr(epgJSON)
                exception.addLogMessage(msg)

            # Cannot show root menu
            exception.addLogMessage(self.language(30010))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False

    def GetAPIUrl(self, parameters):
        # {'api':'ddl', 'type':'basic'} => www.apiRoot.com/api/ddl/type/basic
        url = apiRoot
        
        for key in parameters:
            url = url + '/' + key + '/' + parameters[key]
            
        return url + self.GetJSONPath()

    def ParseCommand(self, mycgi):
        self.log(u"", xbmc.LOGDEBUG)
        (channel, url) = mycgi.Params( u'channel', u'url') 
       
        if channel <> '' and url <> '':
            #return self.PlayChannel(channel, url)
            return self.PlayVideoWithDialog(self.PlayChannel, (channel, url))


    def ShowChannelList(self, url, ddlJSON, epgJSON):
    
        channelDetails = self.ParseEPGData(epgJSON)
        
        soup = BeautifulSoup(ddlJSON['data'])

        listItems = []

        anchors=soup.findAll('a')
        for anchor in anchors:
            try:
                playerIndex = anchor['href'].index('#') + 1
                slug = anchor['href'][playerIndex:]

                if slug in channelToStream.keys():
                    (label, description, logo) = self.GetListItemDataForSlug(channelDetails, slug)
                    newLabel = anchor.text + " " + label
                    
                    newListItem = xbmcgui.ListItem( label=newLabel )
                    newListItem.setThumbnailImage(logo)
                    channelUrl = self.GetURLStart() + u'&channel=' + slug + u'&url=' + mycgi.URLEscape(url)
                    
                    infoLabels = {'Title': newLabel, 'Plot': description, 'PlotOutline': description}
        
                    newListItem.setInfo(u'video', infoLabels)
                    listItems.append( (channelUrl, newListItem, False) )
            except (Exception) as exception:
                # Problem getting details for a particular channel, show a warning and keep going 
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
    
                # Error processing channel 
                message = self.language(32350)
            
                try:
                    message = message + u" " + anchor.text
                    #message = message.encode('utf8')
                except NameError:
                    pass
                      
                exception.addLogMessage(message)
                exception.process(severity = self.logLevel(xbmc.LOGWARNING))
            

        xbmcplugin.addDirectoryItems( handle=self.pluginhandle, items=listItems )
        xbmcplugin.endOfDirectory( handle=self.pluginhandle, succeeded=True )
        
        return True

    def GetTimeCutOffs(self):
        offset = int(self.addon.getSetting( u'AerTV_epg_offset' ))
        startCutOff =  datetime.now() + timedelta(hours=offset)
        startCutOff = startCutOff.replace(second=0,microsecond=0)

        # round time
        if startCutOff.minute > 29:
            startRound = startCutOff.replace(minute=30)
        else:
            startRound = startCutOff.replace(minute=0)
            
        endCutOff = startRound + timedelta(hours=2)

        return (startCutOff, endCutOff)

    def GetEPGDetails(self, channelEntry, startCutOff, endCutOff):
        detail = [channelEntry['channel']['logo']]
        videoCount = 0

        self.log("startCutOff: %s, endCutOff: %s" % (repr(startCutOff), repr(endCutOff)), xbmc.LOGDEBUG)
        for video in channelEntry['videos']:
            try:
                self.log("repr(datetime): " + repr(datetime))
                self.log("video: " + utils.drepr(video))
                self.log("video['starttime']: " + video['starttime'])

                try:
                    startTime = datetime.strptime(video['starttime'], TIME_FORMAT)
                    endTime = datetime.strptime(video['endtime'], TIME_FORMAT)
                except TypeError:
                    startTime = datetime.fromtimestamp(time.mktime(time.strptime(video['starttime'], TIME_FORMAT)))
                    endTime = datetime.fromtimestamp(time.mktime(time.strptime(video['endtime'], TIME_FORMAT)))
                    
#                    self.log("video['starttime']: %s, startTime: %s" % (video['starttime'], repr(startTime)))
#                    self.log("video['endtime']: %s, endTime: %s" % (video['endtime'], repr(endTime)))
                
                if startTime >= startCutOff and startTime < endCutOff:
                    self.log("startTime >= startCutOff and startTime < endCutOff", xbmc.LOGDEBUG)
                    videoCount = videoCount + 1
    
                    if endTime > endCutOff:
                        self.log("endTime > endCutOff", xbmc.LOGDEBUG)
                        # Add "Now ... Ends at ..." if count is 0, or "Next..."
                        detail.append(video) 
                        break
                    else:
                        self.log("endTime <= endCutOff", xbmc.LOGDEBUG)
                        # Add Now .../Next ... depending on count
                        detail.append(video) 
    
                elif startTime < startCutOff and endTime > startCutOff:
                    self.log("startTime < startCutOff and endTime > startCutOff", xbmc.LOGDEBUG)
                    videoCount = videoCount + 1
    
                    # Add Now .../Next ... depending on count
                    detail.append(video)
                else:
                    self.log("Ignoring video: " + video['name'])
                    
                if (videoCount > 1):
                    break
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
    
                self.log("video: %s" % repr(video))
                
                # Error processing EPG entry
                exception.addLogMessage(self.language(20690))
                exception.printLogMessages(severity = xbmc.LOGWARNING)

        return detail
    
    #TODO Consider breaking the epgJSON processing into a separate class
    def ParseEPGData(self, epgJSON):
        (startCutOff, endCutOff) = self.GetTimeCutOffs()
        channelDetails = {}
    
        # Using slug as the identifier for each channel, create a dictionary that allows details of each channel to be looked up by slug.
        for channelEntry in epgJSON['data']:
            slug = channelEntry['channel']['slug']
            
            detail = self.GetEPGDetails(channelEntry, startCutOff, endCutOff)
                 
            """
            # Now
            if len(channelEntry['videos']) > 0:
                detail.append(channelEntry['videos'][0])

                # Next
                if len(channelEntry['videos']) > 1:
                    detail.append(channelEntry['videos'][1])

            """
            channelDetails[slug] = detail

        return channelDetails

    def ParseEPGDataForOneChannel(self, slug, epgJSON):
        (startCutOff, endCutOff) = self.GetTimeCutOffs()

        self.log("\n\nepgJSON: %s\n\n" % utils.drepr(epgJSON), xbmc.LOGDEBUG)

        for channelEntry in epgJSON['data']:
            if slug == channelEntry['channel']['slug']:
                self.log("\n\nchannelEntry: %s\n\n" % utils.drepr(channelEntry), xbmc.LOGDEBUG)

                detail = self.GetEPGDetails(channelEntry, startCutOff, endCutOff)
                
                """
                # Now
                if len(channelEntry['videos']) > 0:
                    detail.append(channelEntry['videos'][0])
    
                    # Next
                    if len(channelEntry['videos']) > 1:
                        detail.append(channelEntry['videos'][1])
                """
                return detail
    
        return None

    def GetListItemData(self, detail):
        description = ''
        if len(detail) == 1:
            label = 'Unknown or Off Air'
            self.log(repr(detail))
        else:
            description = detail[1]['description']
            label = detail[1]['name']
            if len(detail) > 2:
                # E.g. "Nuacht [18:00 Six One]"
                startTime = strptime(detail[2]['starttime'], TIME_FORMAT)
                label = "   " + label + "   [  " + strftime("%H:%M", startTime) + "  " + detail[2]['name']  + "  ]"
            else:
                # E.g. "Nuacht [  Ends at 18:00  ]"
                endTime = strptime(detail[1]['endtime'], TIME_FORMAT)
                label = "   " + label + "   [  Ends at " + strftime("%H:%M", endTime) + "  ]"
        
        return label, description, detail[0]

        
    def GetListItemDataForSlug(self, channelDetails, slug):
        detail = channelDetails[slug]

        return self.GetListItemData(detail)
    

    def PlayChannel(self, channel, epgUrl):
        
        try:
            jsonData = None
            values = {'api':'player', 'type':'name', 'val':channel}
            url = self.GetAPIUrl(values)
        
            # "Getting channel information"
            self.dialog.update(10, self.language(32730))

            jsonData = self.httpManager.GetWebPage(url, 20000)
            jsonText = utils.extractJSON (jsonData)
            playerJSON=simplejson.loads(jsonText)
            self.log("json data:" + unicode(playerJSON))
            
            playerId = playerJSON['data']['playerId']
            publisherId = playerJSON['data']['publisherId']
            playerKey = playerJSON['data']['playerKey']
    
            viewExperienceUrl = urlRoot + '/#' + channel
            
            #streamType = self.addon.getSetting( u'AerTV_stream_type' )
            #self.log(u"Stream type setting: " + streamType)
            
            try:
                if self.dialog.iscanceled():
                    return False
                # "Getting stream url"
                self.dialog.update(25, self.language(32740))
                streamUrl = self.GetStreamUrl(playerKey, viewExperienceUrl, playerId, contentRefId = channel)
                self.log("streamUrl: %s" % streamUrl)
            except (Exception) as exception:
                if not isinstance(exception, LoggingException):
                    exception = LoggingException.fromException(exception)
    
                self.log(" channel: %s" % channel)
                if channel in channelToStream:
                    streamUrl = defaultRTMPUrl + channelToStream[channel]
        
                    # Error getting rtmp url. Using default: %s
                    exception.addLogMessage(self.language(32320) % streamUrl)
                    exception.printLogMessages(severity = xbmc.LOGWARNING)
                else:
                    # Error getting rtmp url.
                    exception.addLogMessage(self.language(32325))
                    # Cannot play video stream
                    raise exception
                
            if self.dialog.iscanceled():
                return False
            # "Getting \"Now Playing\" data
            self.dialog.update(35, self.language(32750))

            # Set up info for "Now Playing" screen
            infoLabels, logo = self.GetInfoLabelsAndLogo(channel, epgUrl)
            
            #RTMP
            if streamUrl.upper().startswith(self.language(32671)):
                playPathIndex = streamUrl.index('&') + 1
                playPath = streamUrl[playPathIndex:]
                qsData = self.GetQSData(channel, playerId, publisherId, playerKey)
                swfUrl = self.GetSwfUrl(qsData)
                pageUrl = urlRoot
                
                if 'videoId' in playerJSON['data']:
                    videoId = playerJSON['data']['videoId']
                else:
                    videoId = playerJSON['data']['offset']['videos'][0]
                    
                app = "rtplive?videoId=%s&lineUpId=&pubId=%s&playerId=%s" % (videoId, publisherId, playerId)
                rtmpVar = rtmp.RTMP(rtmp = streamUrl, app = app, swfUrl = swfUrl, playPath = playPath, pageUrl = pageUrl, live = True)
                self.AddSocksToRTMP(rtmpVar)
                
                self.Play(infoLabels, logo, rtmpVar)            
            else:
                self.Play(infoLabels, logo, url = streamUrl)
            return True
       
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if jsonText is not None:
                msg = "jsonText:\n\n%s\n\n" % jsonText
                exception.addLogMessage(msg)
            
            # Error preparing or playing stream
            exception.addLogMessage(self.language(32340))
            exception.process(severity = self.logLevel(xbmc.LOGERROR))
            return False


    def GetInfoLabelsAndLogo(self, channel, epgUrl):
        infoLabels = None
        logo = None
        
        try:
            epgJSON = self.GetEpgJSON(epgUrl)
            details = self.ParseEPGDataForOneChannel(channel, epgJSON)
            (label, description, logo) = self.GetListItemData(details)
    
            infoLabels = {u'Title': label, u'Plot': description, u'PlotOutline': description}
        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            # Error getting title and logo info for %s
            exception.addLogMessage(self.language(32370) % channel)
            exception.process(severity = xbmc.LOGWARNING)

        return infoLabels, logo

        
    def GetEpgJSON(self, url):
        epgJSONText = self.httpManager.GetWebPage(url, 300)

        epgJSONText = utils.extractJSON (epgJSONText)
        epgJSON = simplejson.loads(epgJSONText)
        
        return epgJSON 
            
    """
    {
        'TTLToken': '',
        'URL': u'https://www.aertv.ie/#rte-one',
        'contentOverrides': [
            {
                'contentId': nan,
                'contentIds': None,
                'contentRefId': u'rte-one',
                'contentRefIds': None,
                'contentType': 0,
                'featuredId': nan,
                'featuredRefId': None,
                'target': u'videoPlayer'
            }
        ],
        'deliveryType': nan,
        'experienceId': 1535624864001.0,
        'playerKey': u'AQ~~,AAABIV9E_9E~,lGDQr89oSbJf6x1rDuEAWKPqTYfK-JH2'
    },
    u'a7ef6ffbfba938b174f5044af3343163a0877c48'
    """
    def GetAmfConst(self):
        return 'a7ef6ffbfba938b174f5044af3343163a0877c48'
    

    def GetQSData(self, videoPlayer, playerId, publisherId, playerKey):
        #TODO Use a default url, in case of exception and log response
        qsdata = {}
        qsdata['width'] = '100%'
        qsdata['height'] = '100%'
        qsdata['flashID'] = 'aertv'
        qsdata['playerID'] = playerId
        qsdata['purl'] = urlRoot
        qsdata['@videoPlayer'] = videoPlayer
        qsdata['playerKey'] = playerKey
        qsdata['publisherID'] = publisherId
        qsdata['bgcolor'] = '#FFFFFF'
        qsdata['isVid'] = 'true'
        qsdata['isUI'] = 'true'
        qsdata['autostart'] = 'true'
        qsdata['wmode'] = 'transparent'
        qsdata['localizedErrorXML'] = 'https://aertv.ie/wp-content/themes/aertv/aertv-custom-error-messages.xml'
        qsdata['templateLoadHandler'] = 'liveTemplateLoaded'
        qsdata['includeAPI'] = 'true'
        qsdata['debuggerID'] = ''
        qsdata['isUI'] = 'true'
        
        return qsdata
    
    #def get_swf_url(self, videoPlayer, playerId, publisherId, playerKey):
        #qsdata['startTime'] = '1358259433367'
    

