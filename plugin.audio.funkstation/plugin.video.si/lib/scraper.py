# -*- coding: utf-8 -*-
# KodiAddon Sports Illustrated (SI)
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'

class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      addonLanguage  = self.addon.getLocalizedString
      html = self.getRequest('http://www.si.com/videos?json=1')
      a = json.loads(html)
      x = json.dumps(a)
      x = x.replace('\\"','"')
      cats = re.compile('<div class="radio-group">.+?<a(.+?)/a>').findall(x)
      for cat in cats:
         (url,name) = re.compile('href="(.+?)".+?>(.+?)<').search(cat).groups(1)
         if '/videos/' in url:
            url = url.replace('/videos/','')
            if url == 'more-sports':
               break
            else:
               ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)


      name = addonLanguage(30003)
      url  = 'swimdaily'
      ilist = self.addMenuItem(name,'GE', ilist, url, self.addonIcon, self.addonFanart, {}, isFolder=True)
      return(ilist)

  def getAddonEpisodes(self,url,ilist):
              Category_url = "http://api.brightcove.com/services/library?callback=&command=search_videos&any=primarycategory%3A"+url+"&page_size=100&video_fields=id%2CshortDescription%2CcreationDate%2CthumbnailURL%2Clength%2Cname&custom_fields=primarycategory%2Csubcategory&sort_by=PUBLISH_DATE%3ADESC&get_item_count=true&token=HYk6klcc_dX8GkFqbW1C2tZHLqgLDxGWBMlica9EroqvNv-skogPlw..&format=json"
              pg = self.getRequest(Category_url)
              a = json.loads(pg)
              for item in a['items']:
                     url   = str(item['id'])
                     name  = item['name']
                     plot  = item['shortDescription']
                     pdate  = item['creationDate']
                     thumb = item['thumbnailURL']
                     ts = int(int(str(int(pdate)))/1000)
                     try:    plot  = datetime.datetime.fromtimestamp(ts).strftime('%a %b %d, %Y %H:%M')+'\n'+plot
                     except: plot = ''
                     try:    thumb = thumb.replace('\\','')
                     except: pass

                     name = name.encode(UTF8)
                     infoList = {}
                     infoList['Title'] = name
                     infoList['Plot']  = plot
                     ilist = self.addMenuItem(name,'GV', ilist, url, thumb, self.addonFanart, infoList, isFolder=False)
              return(ilist)


  def getAddonVideo(self,url):
            url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=myExperience&bgcolor=%23FFFFFF&playerID=2157889318001&playerKey=AQ~~,AAAB9mw57HE~,xU4DCdZtHhuasNZF5WPK5LWKKRK4p1HG&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+url+'&secureConnections=true&secureHTMLConnections=true'
            html = self.getRequest(url)
            m = re.compile('experienceJSON = (.+?)\};').search(html)
            a = json.loads(html[m.start(1):m.end(1)+1])

            try:
                 b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['IOSRenditions']
                 u =''
                 rate = 0
                 for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
                 b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
                 for c in b:
                    if c['encodingRate'] > rate:
                       rate = c['encodingRate']
                       u = c['defaultURL']
                 if rate == 0:
                     try:
                        u = a['data']['programmedContent']['videoPlayer']['mediaDTO']['FLVFullLengthURL']
                     except:
                        u = ''
                 xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=u))

            except:
                 pass

