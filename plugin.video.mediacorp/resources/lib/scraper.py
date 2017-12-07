# -*- coding: utf-8 -*-
# Kodi Addon for Mediacorp
#
from t1mlib import t1mAddon
import json
import re
import urllib
import urllib2
import cookielib
import xbmcplugin
import xbmcgui
import datetime
import HTMLParser
import xbmc
import os
import sys

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):
   html = self.getRequest('http://video.toggle.sg/en/catchup-listing')
   cats = re.compile('<div class="megaslider-holder tgtabs.+?href=".+?">(.+?)<.+?data-ajax-url="(.+?)".+?<div id="preloader">',re.DOTALL).findall(html)

   infoList = {}
   for name,url in cats:
      name = name.strip()
      if not url.startswith('http'):
          url = 'https://video.toggle.sg'+url
      else:
          continue
      infoList['Title'] = name
      infoList['Plot']  =  name
      infoList['mediatype'] = 'file'
      ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonShows(self,url,ilist):
   url   = uqp(url)
   html  = self.getRequest(url)
   blob = re.compile('bandData =(.+?)toggle.functions',re.DOTALL).search(html)
   if blob is not None:
       blob = blob.group(1)
       blob = blob.replace('JSON.stringify({})',"''")
       blob = blob.strip()
       blob = blob.replace('}',',').replace('{','')
       kpairs = re.compile('(.+?)\:(.+?),').findall(blob)
       u = ''
       for kkey,kval in kpairs:
          kkey=kkey.strip()
          kval=kval.strip()
          u = u+'&%s=%s' % (kkey,kval.replace('"','').replace("'",''))
          u = re.sub(r'pageSize=[0-9]*', 'pageSize=300', u)
       url = 'http://video.toggle.sg/en/blueprint/servlet/toggle/bandlist?%s' % u
       html = self.getRequest(url)
       shows = re.compile('<div class="tg-teaser-item".+?href="(.+?)".+?src="(.+?)".+?<h6 class.+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
   else:
       shows = re.compile('<div class="tg-teaser-item".+?href="(.+?)".+?srcset="(.+?)".+?<h6 class.+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
   for (url,thumb,name) in shows:
       name = name.decode(UTF8)
       infoList = {}
       if not (thumb.startswith('http')):
           thumb = 'http://video.toggle.sg'+thumb
       name = name.strip()
       name = h.unescape(name)
       infoList['Title'] = name
       infoList['Plot'] = name
       infoList['TVShowTitle'] = name
       infoList['mediatype'] = 'tvshow'
       if ('/movies/' in url) or ('/extras' in url):
           ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
       else:
           ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   url = uqp(url)
   showName = xbmc.getInfoLabel('ListItem.TVShowTitle')
   html = self.getRequest(url)
   url = re.compile('<div class="tg-microsite-link card ".+?href="(.+?)"', re.DOTALL).search(html).group(1)
   url += '/episodes'
   html = self.getRequest(url)
   parms = re.compile('toggle.functions.ajaxEpisodeListingPage\((.+?)\)', re.DOTALL).search(html).group(1)
   parms = parms.split(',')
   url = 'http://tv.toggle.sg/en/blueprint/servlet/toggle/paginate?pageSize=200&pageIndex=0&contentId=%s&navigationId=%s&isCatchup=1' % (parms[3].strip(), parms[4].strip())
   html = self.getRequest(url)
   epis = re.compile('<div class="img-holder">.+?src="(.+?)".+?ref="(.+?)">(.+?)<.+?<p>(.+?)</p', re.DOTALL).findall(html)
   for (thumb,url,name,plot) in epis:
      infoList={}
      name = name.replace('\n','').strip()
      vid = url.rsplit('/',1)[1]
      if not (thumb.startswith('http')): thumb = 'http://video.toggle.sg'+thumb
      infoList['Plot'] = h.unescape(plot.decode(UTF8))
      infoList['Title'] = h.unescape(name)
      infoList['TVShowTitle'] = showName
      infoList['mediatype'] = 'episode'
      fanart = thumb
      ilist = self.addMenuItem(name,'GV', ilist, vid, thumb, fanart, infoList, isFolder=False)
   return(ilist)


 def getAddonVideo(self,url):
     vid = url
     vurl = 'http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id='+vid+'&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22'+vid+'%22%2C%22iMediaID%22%3A%22'+vid+'%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback='
     html = self.getRequest(vurl)
     m = re.compile('kalturaIframePackageData = (.+?)};',re.DOTALL).search(html)
     x = html[m.start(1):m.end(1)+1].replace('\\','')
     x = re.compile('"Files"\:(.+?),"Tags"', re.DOTALL).search(x).group(1)
     a = json.loads(x)
     u = None
     for c in ['STB Main','Main','HLS_Web','HLS_Tablet','iPad Main']:
         for b in a:
             if b['Format'] == c:
                  u = b['URL']
                  break
         if not (u is None):
             break
     if ( u is None or u.endswith('.wvm')):
         xbmcgui.Dialog().notification(self.addonName, 'No Video Found', self.addonIcon, 5000)
         return
     liz = xbmcgui.ListItem(path = u)
     html = self.getRequest('https://sub.toggle.sg/toggle_api/v1.0/apiService/getSubtitleFilesForMedia?mediaId=%s' % vid)
     subfile = json.loads(html)
     subfiles = []
     for a in subfile.get('subtitleFiles'):
         subfiles.append(a['subtitleFileUrl'])
     liz.setSubtitles(subfiles)
     liz.setProperty('inputstreamaddon','inputstream.adaptive')
     liz.setProperty('inputstream.adaptive.manifest_type','hls')
     liz.setMimeType('application/x-mpegURL')
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

