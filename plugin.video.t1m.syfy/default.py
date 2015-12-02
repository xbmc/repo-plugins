# -*- coding: utf-8 -*-
# KodiAddon (Syfy)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import urllib2
import xbmcplugin
import xbmcgui
import datetime
import HTMLParser

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):

   __language__  = self.addon.getLocalizedString
   meta = self.getAddonMeta()
   try:    i = len(meta['shows'])
   except: meta['shows']={}
   epiHTML = self.getRequest('http://www.syfy.com/episodes')
   posterHTML = self.getRequest('http://www.syfy.com/shows')
   posters = re.compile('<div class="grid-image-above">.+?<img  srcset="(.+?)".+?class="title">.+?>(.+?)<',re.DOTALL).findall(posterHTML)
   shows = re.compile('<div class="show id.+?<h3>(.+?)<.+?</div',re.DOTALL).findall(epiHTML)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, __language__(30101))
   pDialog.update(0)
   numShows = len(shows)

   for i, name in list(enumerate(shows, start=1)):
       poster = None
       for pimg, pname in posters:
          if pname == name:
            poster = pimg
            break

       m  = re.compile('<div class="show id.+?<h3>'+name+'</h3>(.+?)</a></div>  </div>  </div>\n    </div>',re.DOTALL).search(epiHTML)
       epis = re.compile('href="(.+?)"',re.DOTALL).findall(epiHTML,m.start(1),m.end(1))
       vcnt = len(epis)
       shurl  = 'http://www.syfy.com%s' % epis[len(epis)-1]

       try:
          (name, poster, infoList) = meta['shows'][shurl]
       except:
          html = self.getRequest(shurl)
          try:
             purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
          except: continue
          purl = 'http:'+purl.replace('&amp;','&')
          html = self.getRequest(purl)
          purl = re.compile('<link rel="alternate" href=".+?<link rel="alternate" href="(.+?)"',re.DOTALL).search(html).group(1)
          purl += '&format=Script&height=576&width=1024'
          html = self.getRequest(purl)
          a = json.loads(html)
          infoList = {}
          infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
          infoList['Aired']       = infoList['Date']
          infoList['MPAA']        = a['ratings'][0]['rating']
          infoList['TVShowTitle'] = name
          infoList['Title']       = name
          infoList['Studio']      = a['provider']
          infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
          infoList['Episode']     = vcnt
          infoList['Year']        = int(infoList['Aired'].split('-',1)[0])
          url = '%s/cast' % shurl.split('/video',1)[0]
          html = self.getRequest(url)
          try:    infoList['Plot'] = re.compile('<div class="field field-name-body.+?<p>(.+?)</p',re.DOTALL).search(html).group(1)
          except: 
             try:    infoList['Plot'] = re.compile('<meta name="description" content="(.+?)"',re.DOTALL).search(html).group(1)
             except: infoList['Plot'] = '%s Episodes' % str(vcnt)
          infoList['cast'] = re.compile('<article class="tile.+?tile-marqee">(.+?)<.+?</article',re.DOTALL).findall(html)
          if len(infoList['cast']) == 0: 
             infoList['cast'] = re.compile('<article class="tile.+?tile-title">(.+?)<.+?</article',re.DOTALL).findall(html)
          infoList['Plot'] = h.unescape(infoList['Plot'].decode(UTF8))
       url = name
       meta['shows'][shurl] = (name, poster, infoList)
       ilist = self.addMenuItem(name,'GE', ilist, url, poster, self.addonFanart, infoList, isFolder=True)
       pDialog.update(int((100*i)/numShows))
   pDialog.close()
   self.updateAddonMeta(meta)
   return(ilist)



 def getAddonEpisodes(self,url,ilist):
   sname = uqp(url)
   __language__  = self.addon.getLocalizedString
   self.defaultVidStream['width'] = 1920
   self.defaultVidStream['height']= 1080
   meta = self.getAddonMeta()
   try:    i = len(meta[sname])
   except: meta[sname]={}

   html = self.getRequest('http://www.syfy.com/episodes')
   m  = re.compile('<div class="show id.+?<h3>'+sname+'</h3>(.+?)<div class="view-footer">',re.DOTALL).search(html)
   fd = re.compile('href="(.+?)/videos').search(html,m.start(1),m.end(1)).group(1)
   epis = re.compile('href="'+fd+'(.+?)"',re.DOTALL).findall(html,m.start(1),m.end(1))
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, __language__(30101))
   pDialog.update(0)
   numShows = len(epis)

   for i, shurl in list(enumerate(epis, start=1)):
    try:
       (name, purl, thumb, fanart, infoList) = meta[sname][shurl]
    except:
      url = 'http://www.syfy.com%s' % fd+shurl
      html = self.getRequest(url)
      purl = re.compile('data-src="(.+?)"',re.DOTALL).search(html).group(1)
      purl = 'http:'+purl.replace('&amp;','&')
      html = self.getRequest(purl)
      purl = re.compile('<link rel="alternate" href=".+?<link rel="alternate" href="(.+?)"',re.DOTALL).search(html).group(1)
      purl += '&format=Script&height=576&width=1024'
      html = self.getRequest(purl)
      a = json.loads(html)
      name    = a['title']
      fanart  = a['defaultThumbnailUrl']
      thumb   = a['defaultThumbnailUrl']

      infoList = {}
      infoList['Date']        = datetime.datetime.fromtimestamp(a['pubDate']/1000).strftime('%Y-%m-%d')
      infoList['Aired']       = infoList['Date']
      infoList['Duration']    = str(int(a['duration']/1000))
      infoList['MPAA']        = a['ratings'][0]['rating']
      infoList['Title']       = a['title']
      infoList['Studio']      = a['provider']
      infoList['Genre']       = (a['nbcu$advertisingGenre']).replace('and','/')
      try:    infoList['Episode']     = a['pl1$episodeNumber']
      except: pass
      try:    infoList['Season']      = a['pl1$seasonNumber']
      except: pass
      try:
         infoList['Plot']     = h.unescape(a["description"])
      except:
         infoList['Plot']     = h.unescape(a["abstract"])
      infoList['Title']       = a['title']
      infoList['TVShowTitle'] = sname
      infoList['Studio']      = a['provider']

    url = purl
    meta[sname][shurl] = (name, purl, thumb, fanart, infoList)
    ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    pDialog.update(int((100*i)/numShows))
   pDialog.close()
   self.updateAddonMeta(meta)
   return(ilist)

 def getAddonVideo(self,url):
    gvu1 = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,25,40,18,12,7,4,2,00.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
    gvu2 = 'https://tvesyfy-vh.akamaihd.net/i/prod/video/%s_,1696,1296,896,696,496,240,306,.mp4.csmil/master.m3u8?__b__=1000&hdnea=st=%s~exp=%s'
    pfu1 = 'http://link.theplatform.com/s/HNK2IC/media/'
    pfparms = '?player=Syfy.com%20Player&policy=2713542&manifest=m3u&formats=flv,m3u,mpeg4&format=SMIL&embedded=true&tracking=true'

    url = uqp(url)
    url = url.replace(' ','%20')
    html = self.getRequest(url)
    a = json.loads(html)
    try:
         suburl = a["captions"][0]["src"]
         url = suburl.split('/caption/',1)[1]
         url = url.split('.',1)[0]
         td = (datetime.datetime.utcnow()- datetime.datetime(1970,1,1))
         unow = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)
         u   =  gvu1 % (url, str(unow), str(unow+60))
         req = urllib2.Request(u.encode(UTF8), None, self.defaultHeaders)
         try:
            response = urllib2.urlopen(req, timeout=20) # check to see if video file exists
         except:
            u   =  gvu2 % (url, str(unow), str(unow+60))
    except:
         url = a['mediaPid']
         url = pfu1+url+pfparms
         html = self.getRequest(url, None, self.defaultHeaders)
         u  = re.compile('<video src="(.+?)"',re.DOTALL).search(html).group(1)
    liz = xbmcgui.ListItem(path = u)
    liz.setSubtitles([self.procConvertSubtitles(suburl)])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon
