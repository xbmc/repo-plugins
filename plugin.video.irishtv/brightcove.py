# -*- coding: utf-8 -*-
import re
import sys
from time import strftime,strptime
import time, random
import urllib
import pyamf
from pyamf import remoting

from datetime import timedelta
from datetime import date
from datetime import datetime
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

import HTMLParser
from BeautifulSoup import BeautifulSoup

from provider import Provider

c_brightcove = u"http://c.brightcove.com"

class BrightCoveProvider(Provider):

    def __init__(self):
        super(BrightCoveProvider, self).__init__()
        self.amfResponse = None
        self.useBitRateSetting = True

    def ChooseBitRate(self, preferredRate, renditions):
        #if len(renditions) < 2:
        #    return None

        rates = {}
        for rendition in renditions:
            rates[rendition['encodingRate']] = rendition
        
        self.log("rates.keys(): %s" % rates.keys())

        #if 0 in rates:
        #    del rates[0]

        if preferredRate is None or preferredRate == -1:
            self.log("min(rates.keys()): %s" % min(rates.keys()))
            return rates[min(rates.keys())]['defaultURL']

        reverseRates = rates.keys()
        reverseRates.sort()
        reverseRates.reverse()

        self.log("reverseRates: %s" % reverseRates)

        for rate in reverseRates:
            self.log("if bitrate >= %s: %s" %( rate, preferredRate >= rate))
            if preferredRate >= rate:
                return rates[rate]['defaultURL']

        return rates[min(rates.keys())]['defaultURL']

    def GetStreamUrl(self, key, url, playerId, contentRefId = None, contentId = None, streamType = "RTMP"):
        self.log("", xbmc.LOGDEBUG)
        try:
            self.amfResponse = None
            self.amfResponse = self.GetEpisodeInfo(key, url, playerId, contentRefId = contentRefId, contentId = contentId)
            name = self.amfResponse['name']
           
            self.log("Name field: " + name)
           
            preferredRate = self.GetBitRateSetting()
           
            self.log("bitrate setting: %s" % preferredRate)
           
            defaultStreamUrl = self.amfResponse['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']

            self.log("defaultStreamUrl: %s" % defaultStreamUrl)
           
            if preferredRate is None and defaultStreamUrl.upper().startswith(streamType):
                return defaultStreamUrl 

            originalRenditions = self.amfResponse['programmedContent']['videoPlayer']['mediaDTO']['renditions']
            self.log("renditions: %s" % utils.drepr(originalRenditions))

            renditions = []
            renditionsOther = []
            for rendition in originalRenditions:
                if rendition['encodingRate'] == 0:
                    continue
                
                if rendition['defaultURL'].upper().startswith(streamType):
                    renditions.append(rendition)
                else:
                    renditionsOther.append(rendition)
            
            if len(renditions) == 0:
                self.log("Unable to find stream of type '%s'" % streamType, xbmc.LOGWARNING)
                renditions = renditionsOther

            self.log("renditions: %s" % utils.drepr(renditions))
            bitrate = self.ChooseBitRate(preferredRate, renditions)

            if bitrate == None:
                return defaultStreamUrl
            
            return bitrate

        except (Exception) as exception:
            if not isinstance(exception, LoggingException):
                exception = LoggingException.fromException(exception)

            if self.amfResponse is not None:
                msg = "self.amfResponse:\n\n%s\n\n" % utils.drepr(self.amfResponse)
                exception.addLogMessage(msg)

            raise exception
                
    def GetEpisodeInfo(self, key, url, playerId, contentRefId = None, contentId = None):
       self.log("", xbmc.LOGDEBUG)
       envelope = self.BuildAmfRequest(key, url, playerId, contentRefId = contentRefId, contentId = contentId)
    
       self.log("POST c.brightcove.com/services/messagebroker/amf?playerKey=%s" % key, xbmc.LOGDEBUG)
       self.log("Log key: %s" % repr(key), xbmc.LOGDEBUG)    

       hub_data = remoting.encode(envelope).read()

       #self.log("hub_data: %s" % utils.drepr(remoting.decode(amfData).bodies[0][1].body), xbmc.LOGDEBUG)    
       #self.log("hub_data: %s" % repr(remoting.decode(hub_data).bodies[0][1].body), xbmc.LOGDEBUG)
       amfData = self.httpManager.PostBinary(c_brightcove.encode("utf8"), "/services/messagebroker/amf?playerKey=" + key.encode('ascii'), hub_data, {'content-type': 'application/x-amf'})
       response = remoting.decode(amfData).bodies[0][1].body

       self.log("response: " + utils.drepr(response), xbmc.LOGDEBUG)

       return response

    def FindRelatedVideos(self, key, playerId, pubId, episodeId, pageSize, pageNumber, getItemCount):
       self.log("", xbmc.LOGDEBUG)
       envelope = self.BuildAmfRequest_FindRelated(key, playerId, pubId, episodeId, pageSize, pageNumber, getItemCount)
    
       self.log("POST c.brightcove.com/services/messagebroker/amf?playerKey=%s pubId=%s" % (key, pubId), xbmc.LOGDEBUG)
       self.log("Log key: %s" % repr(key), xbmc.LOGDEBUG)    

       hub_data = remoting.encode(envelope).read()

       #self.log("hub_data: %s" % utils.drepr(remoting.decode(amfData).bodies[0][1].body), xbmc.LOGDEBUG)    
       #self.log("hub_data: %s" % repr(remoting.decode(hub_data).bodies[0][1].body), xbmc.LOGDEBUG)
       amfData = self.httpManager.PostBinary(c_brightcove.encode("utf8"), "/services/messagebroker/amf?playerKey=" + key.encode('ascii'), hub_data, {'content-type': 'application/x-amf'})
       response = remoting.decode(amfData).bodies[0][1].body

       self.log("response: " + utils.drepr(response), xbmc.LOGDEBUG)

       return response


    def GetAmfClassHash(self, className):
        return None
    
    def BuildAmfRequest(self, key, url, exp_id, contentRefId = None, contentId = None):
       self.log('ContentRefId:' + str(contentRefId) + ', ExperienceId:' + str(exp_id) + ', URL:' + url)  

       method = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience"
       className = method[0:method.rfind('.')]
       hashValue = self.GetAmfClassHash(className)

       self.log('hashValue:' + str(hashValue))
 
       pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
       pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
       content_override = ContentOverride(contentRefId = contentRefId, contentId = contentId)
       viewer_exp_req = ViewerExperienceRequest(url, [content_override], int(exp_id), key)
    
       print content_override.tostring()
       print viewer_exp_req.tostring()
    
       env = remoting.Envelope(amfVersion=3)
       env.bodies.append(
          (
             "/1",
             remoting.Request(
                target=method,
                body=[hashValue, viewer_exp_req],
                envelope=env
             )
          )
       )
       return env

    def BuildAmfRequest_FindRelated(self, key, exp_id, pubId, videoPlayer, pageSize, pageNumber, getItemCount):
       self.log('ExperienceId:' + str(exp_id))  

       method = "com.brightcove.player.runtime.PlayerSearchFacade.findRelatedVideos"
       className = method[0:method.rfind('.')]
       hashValue = self.GetAmfClassHash(className)

       self.log('hashValue:' + hashValue)
 
       pageSize = 12
       pageNumber = 0
       getItemCount = False

       env = remoting.Envelope(amfVersion=3)
       env.bodies.append(
          (
             "/1",
             remoting.Request(
                target=method,
                body=[hashValue, int(exp_id), pubId, videoPlayer, pageSize, pageNumber, getItemCount],
#                body=[hashValue, "Nuacht", 1, 0, False, None, None, None, None, None],
                envelope=env
             )
          )
       )
       return env

    def GetSwfUrl(self, qsData):
        self.log("", xbmc.LOGDEBUG)
        url = c_brightcove + "/services/viewer/federated_f9?&" + urllib.urlencode(qsData)
        response = self.httpManager.GetHTTPResponse(url)

        location = response.url
        base = location.split("?",1)[0]
        location = base.replace("BrightcoveBootloader.swf", "federatedVideoUI/BrightcoveBootloader.swf")
        return location
        

    
class ViewerExperienceRequest(object):
   def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken=''):
      self.TTLToken = TTLToken
      self.URL = URL
      self.deliveryType = float(0)
      self.contentOverrides = contentOverrides
      self.experienceId = experienceId
      self.playerKey = playerKey


   def tostring(self):
      print "TTLToken: %s, URL: %s, deliveryType: %s, contentOverrides: %s, experienceId: %s, playerKey: %s" % (self.TTLToken, self.URL, self.deliveryType, self.contentOverrides, self.experienceId, self.playerKey)

class ContentOverride(object):
   def __init__(self, contentId = float(0), contentIds = None, contentRefId = None, contentRefIds = None, contentType = 0, featureId = float(0), featuredRefId = None, contentRefIdtarget='videoPlayer'):
      self.contentType = contentType
      self.contentId = contentId
      self.target = contentRefIdtarget
      self.contentIds = contentIds
      self.contentRefId = contentRefId
      self.contentRefIds = contentRefIds
      self.featureId = featureId
      self.featuredRefId = None

   def tostring(self):
      print "contentType: %s, contentId: %s, target: %s, contentIds: %s, contentRefId: %s, contentRefIds: %s, contentType: %s, featureId: %s, featuredRefId: %s, " % (self.contentType, self.contentId, self.target, self.contentIds, self.contentRefId, self.contentRefIds, self.contentType, self.featureId, self.featuredRefId)
