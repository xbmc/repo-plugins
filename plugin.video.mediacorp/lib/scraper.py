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
   home         = self.addon.getAddonInfo('path').decode(UTF8)
   nextIcon     = xbmc.translatePath(os.path.join(home, 'resources','media','next.png'))


   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

   liveList = []

   for name, thumb, url, epgid in liveList:
      infoList = {}
      name = '%s LIVE' % name
      try:
         html = self.getRequest('http://www.toggle.sg/en/channelguide/%s' % epgid)
         (title, desc) = re.compile('<div class="epg--channel__item is-active on-now">.+?<a class="no-hover">(.+?)</a>.+?<p class="epg__desc">(.+?)</p', re.DOTALL).search(html).groups()
         infoList['Title'] = name
         infoList['Plot']  = '[COLOR blue]%s[/COLOR]\n%s' % (title.strip(), desc.strip())
      except:
         pass
      ilist = self.addMenuItem(name, 'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)

   html = self.getRequest('http://video.toggle.sg/en/tvshows/mediacorpcollection')
   cu   = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
   html = self.getRequest('http://video.toggle.sg/en/catchup-listing')
   cats = re.compile('<h5 class="collapsible__title">.+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
   cats.extend(cu)
   infoList = {}
   for url, name in cats:
      name = name.strip()
      infoList['Title'] = name
      infoList['Plot']  =  name
      ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getAddonShows(self,url,ilist):
   url   = uqp(url)
   html  = self.getRequest(url)
   blob = re.compile('bandData =(.+?)toggle.functions',re.DOTALL).search(html).group(1)
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
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   numShows = len(shows)
   for i,(url,thumb,name) in list(enumerate(shows, start=1)):
       name = name.decode(UTF8)
       infoList = {}
       if not (thumb.startswith('http')): thumb = 'http://video.toggle.sg'+thumb
       name = name.strip()
       infoList['Title'] = name
       infoList['Plot'] = name
       if ('/movies/' in url) or ('/extras' in url):
           ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
       else:
           ilist = self.addMenuItem(name,'GE', ilist, url, thumb, self.addonFanart, infoList, isFolder=True)
       pDialog.update(int((100*i)/numShows))
   pDialog.close()
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   url   = uqp(url)
   meta = self.getAddonMeta()
   try:    i = len(meta[url])
   except: meta[url]={}

   html = self.getRequest(url)
   try: 
      epis = re.compile('<li class="fixed-height__item.+?href="(.+?)".+?data-src="(.+?)".+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
      if len(epis) == 0: raise ValueError('No items in dir')
   except:
     try:
      u1,u2,u3 = re.compile('toggle.functions.showEpisodeSidebarInEpisodeDetail.+?"(.+?)".+?"(.+?)".+?"(.+?)"', re.DOTALL).search(html).groups()
      sburl = 'http://video.toggle.sg%s?id=%s&navigationId=%s&isCatchup=true&view=ajaxEpisodeSidebar' % (u1,u2,u3)
      html = self.getRequest(sburl)
      epis = re.compile('<li class="fixed-height__item.+?href="(.+?)".+?data-src="(.+?)".+?href=.+?">(.+?)<.+?</div',re.DOTALL).findall(html)
     except: return(ilist)
   numShows = len(epis)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   dirty = False
   for i,(url,thumb,name) in list(enumerate(epis, start=1)):
      infoList={}
      name = name.replace('\n','').strip()
      vid = url.rsplit('/',1)[1]
      if not (thumb.startswith('http')): thumb = 'http://video.toggle.sg'+thumb
      try:
         (name, vid, thumb, infoList) = meta[url]
      except:
         vurl = 'http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id='+vid+'&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22'+vid+'%22%2C%22iMediaID%22%3A%22'+vid+'%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback='
         html = self.getRequest(vurl)
         html = re.compile('kalturaIframePackageData = (.+?)};',re.DOTALL).search(html).group(1)
         html = html+'}'
         html = html.replace('\\','')
         try:
           a = json.loads(html)
           a = a['entryResult']['meta']
         except: continue
         tags = {}
         for b in a['partnerData']['Tags'] : tags[b['Key']] = b['Value']
         metas = {}
         try:
            for b in a['partnerData']['Metas']: metas[b['Key']] = b['Value']
         except: pass
         thumb = a['thumbnailUrl']
#         name  = a['name'].decode(UTF8)
         name  = a['name']
         infoList['Date']  = a['startDate'].split('T',1)[0]
         infoList['Aired'] = infoList['Date']
         try: infoList['duration']    = int(a['duration'])
         except: pass
         try: 
            infoList['MPAA'] = tags['Rating']
            if tags['Rating'] == 'PG' : infoList['MPAA'] = 'TV-PG'
         except: pass
         try:    infoList['TVShowTitle'] = tags['Series name']
         except: pass
         try: 
            infoList['Title'] = metas['Episode name']
            name = infoList['Title']
         except: infoList['Title']= name
         try: infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
         except: pass

         try: infoList['Studio'] = tags['Provider']
         except: pass
         try: infoList['Genre'] = tags['Genre']
         except: pass
         try:  
            infoList['Season'] = int(metas['Season number'])
            if infoList['Season'] == 0: infoList['Season'] = infoList['Year']
         except: pass
         try: infoList['Episode']     = int(metas['Episode number'])
         except: pass
         infoList['Plot'] = h.unescape(a['description'])
      fanart = thumb
      ilist = self.addMenuItem(name,'GV', ilist, vid, thumb, fanart, infoList, isFolder=False)
      meta[url] = (name, vid, thumb, infoList)
      dirty = True
      pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)


 def getAddonVideo(self,url):
     vid = url
     vurl = 'http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id='+vid+'&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22'+vid+'%22%2C%22iMediaID%22%3A%22'+vid+'%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback='
     html = self.getRequest(vurl)
     m = re.compile('kalturaIframePackageData = (.+?)};',re.DOTALL).search(html)
     a = json.loads(html[m.start(1):m.end(1)+1].replace('\\',''))
     a = a['entryResult']['meta']
     a = a['partnerData']['Files']
     u =''
     if self.addon.getSetting('vid_res') == '1':
        for b in a:
           vtype = 'STB Main'
           if b['Format'] == vtype:
              u = b['URL']
              break
        req = urllib2.Request(u, None, self.defaultHeaders)
        try:
           response = urllib2.urlopen(req, timeout=40)
        except:
           u = ''
     if u == '':
        for b in a:
           vtype = 'iPad Main'
           if b['Format'] == vtype:
              u = b['URL']
              break
     if ( u == '' or u.endswith('.wvm')):
         u=''
         xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, 'No Playable Video Found' , 5000) )
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))

