# -*- coding: utf-8 -*-
# KodiAddon (TCM)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

    pg = self.getRequest('http://api.tcm.com//tcmws/v1/vod/tablet/catalog/orderBy/title.jsonp')
    a = json.loads(pg)
    epis = a['tcm']['titles']
    for b in epis:
       url   = b['vod']['contentId']
       name  = b['name']
       try: thumb = b['imageProfiles'][1]['url']
       except: thumb = b['vod']['associations']['franchises'][0]['imageProfiles'][0]['url']
       fanart = thumb
       infoList = {}
       infoList['Title'] = name
       try:    infoList['Plot'] = b['description']
       except: pass
       try:    infoList['Duration'] = str(int(b['runtimeMinutes'])*60)
       except: pass
       try:    infoList['Year'] = b['releaseYear']
       except: pass
       try:    infoList['director'] = b['tvDirectors'].strip('.')
       except: pass
       try:    infoList['cast'] = b['tvParticipants'].split(',')
       except: pass
       try:    infoList['genre'] = b['tvGenres']
       except: pass
       try:    infoList['mpaa'] = 'Rated: %s' % b['tvRating']
       except: pass
       ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)


  def getAddonVideo(self,vid):

    pg = self.getRequest('http://www.tcm.com/tveverywhere/services/videoXML.do?id=%s' % vid)
    url = re.compile('<file bitrate="2048".+?>(.+?)<',re.DOTALL).search(pg).group(1)
    filename = url[1:len(url)-4]

    a=re.compile('<akamai>(.+?)</akamai>', re.DOTALL).search(pg).group(1)
    rtmpServer = re.compile('<src>(.+?)</src>',re.DOTALL).search(a).group(1).split('://')[1]
    aifp = re.compile('<aifp>(.+?)</aifp>', re.DOTALL).search(a).group(1)
    window = re.compile('<window>(.+?)</window>', re.DOTALL).search(a).group(1)
    tokentype = re.compile('<authTokenType>(.+?)</authTokenType>', re.DOTALL).search(a).group(1)

    udata = urllib.urlencode({'aifp': aifp, 'window': window, 'authTokenType': tokentype, 'videoId' : vid, 'profile': 'tcm', 'path': filename.replace('mp4:','')})

    pg = self.getRequest('http://www.tbs.com/processors/cvp/token.jsp', udata)
    authtoken = re.compile('<token>(.+?)</').search(pg).group(1)

    swfURL = 'http://z.cdn.turner.com/xslo/cvp/plugins/akamai/streaming/osmf1.6/2.10/AkamaiAdvancedStreamingPlugin.swf'
    url = 'rtmpe://' + rtmpServer + '?' + authtoken + ' playpath=' + filename + ' swfurl=' + swfURL + ' swfvfy=true'
    super(myAddon, self).getAddonVideo(url)


# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon

