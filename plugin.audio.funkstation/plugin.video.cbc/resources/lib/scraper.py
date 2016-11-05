# -*- coding: utf-8 -*-
# KodiAddon (CBC.ca)
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
import zlib
import sys
import xbmc

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):
   infoList = {}
   html = self.getRequest('http://www.cbc.ca/player/tv')
   html = re.compile('<section class="section-cats full">(.+?)</section>', re.DOTALL).search(html).group(1)
   shows = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(html)
   shows.append(('/player/news','News'))
   shows.append(('/player/Sports','Sports'))
   shows.append(('/player/news/TV%20Shows/The%20National/Latest%20Broadcast','The National - Latest Broadcast'))

   for url, name in shows:
      ilist = self.addMenuItem(name,'GC', ilist, url+'|'+name, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)


 def getAddonCats(self,lurl,ilist):
   infoList = {}
   url  = uqp(lurl)
   xurl = url.split('|',1)
   gcurl = urllib.quote(xurl[0])
   gcurl = gcurl.replace('%3A',':',1)
   catname = xurl[1]
   html  = self.getRequest('http://www.cbc.ca%s' % gcurl)
   try:    
           html = re.compile('<section class="category-subs full">(.+?)</section', re.DOTALL).search(html).group(1)
           shows = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
   except:
      try:
           html = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
           ilist = self.getAddonEpisodes(lurl, ilist)
           return(ilist)
      except:
           html = re.compile('<section class="section-cats full">(.+?)</section', re.DOTALL).search(html).group(1)
           shows = re.compile('a href="(.+?)">(.+?)<', re.DOTALL).findall(html)
        

   for url, name in shows:
      ilist = self.addMenuItem(name,'GE', ilist, url+'|'+catname, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

  

 def getAddonShows(self,url,ilist):
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
   self.defaultVidStream['width']  = 960
   self.defaultVidStream['height'] = 540

   url   = uqp(url)
   geurl, sname = url.split('|',1)
   geurl = urllib.quote(geurl)
   geurl = geurl.replace('%3A',':',1)
   meta = self.getAddonMeta()
   try:    i = len(meta[sname])
   except: meta[sname]={}
   html  = self.getRequest('http://www.cbc.ca%s' % geurl)
   html  = re.compile('<section class="category-content full">(.+?)</section', re.DOTALL).search(html).group(1)
   if '<li class="active">' in html:
        return(self.getAddonShows(url, ilist))

   epis  = re.compile('<a href="(.+?)" aria-label="(.+?)".+?src="(.+?)".+?</a', re.DOTALL).findall(html)
   numShows = len(epis)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   dirty = False
   for i,(url,name,img) in list(enumerate(epis, start=1)):
     name = name.decode('utf-8','replace')
     try:
         (name, img, infoList) = meta[sname][url] 
     except:
         infoList={}
         try:
            html = self.getRequest(url)
            try:
                plot = re.compile('<meta name="description" content="(.+?)"', re.DOTALL).search(html).group(1)
            except:
                plot = name
         except: plot=name
         infoList['TVShowTitle'] = sname
         infoList['Title'] = name
         try:    infoList['Plot'] = h.unescape(plot.decode('utf-8'))
         except: infoList['Plot'] = h.unescape(plot)

         meta[sname][url] = (name, img, infoList)
         dirty = True

     fanart = img
     ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
     pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)



 def getProxyRequest(self, url):
    USER_AGENT    = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
    headers = {'User-Agent':USER_AGENT, 
                 'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
                 'Accept-Encoding':'gzip,deflate,sdch',
                 'Accept-Language':'en-US,en;q=0.8'} 
    if (self.addon.getSetting('us_proxy_enable') == 'true'):
       us_proxy = 'http://%s:%s' % (self.addon.getSetting('us_proxy'), self.addon.getSetting('us_proxy_port'))
       proxy_handler = urllib2.ProxyHandler({'http':us_proxy})
       if self.addon.getSetting('us_proxy_pass') <> '' and self.addon.getSetting('us_proxy_user') <> '':
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, us_proxy, self.addon.getSetting('us_proxy_user'), self.addon.getSetting('us_proxy_pass'))
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
            opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
       else:
            opener = urllib2.build_opener(proxy_handler)
    else:
       opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    req = urllib2.Request(url.encode(UTF8), None, headers)
    try:
       response = urllib2.urlopen(req, timeout=120)
       page = response.read()
       if response.info().getheader('Content-Encoding') == 'gzip':
           page = zlib.decompress(page, zlib.MAX_WBITS + 16)

    except urllib2.URLError, e:
       xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (self.addonName, e , 5000) )
       page = ""
    return(page)


 def getAddonVideo(self,lurl):
            vid = uqp(lurl)
            vid = vid.rsplit('/',1)[1]
            html = self.getRequest('http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?q=*&byGuid=%s' % vid)
            a = json.loads(html)
            a = a['entries'][0]['content']
            u = ''
            vwid = 0
            for b in a:
               if b['width'] >= vwid:
                  u = b['url']
                  vwid = b['width']

            u = u.split('/meta.smil',1)[0]
            suburl = u+'?mbr=true&format=preview&feed=Player%20Selector%20-%20Prod'
            u = u + '?mbr=true&manifest=m3u&feed=Player%20Selector%20-%20Prod'
            html = self.getProxyRequest(u)
            u = re.compile('<video src="(.+?)"', re.DOTALL).search(html).group(1)
            html = self.getProxyRequest(u)
            try:
                urls = re.compile('BANDWIDTH=(.+?),.+?\n(.+?)\n', re.DOTALL).findall(html)
                x = 0
                for (bw, v) in urls:
                   if int(bw)> x:
                     x = int(bw)
                     yy = v
       
                u = yy.strip()  
            except:
                u = re.compile('CODECS=".+?"(.+?)#', re.DOTALL).search(html).group(1)
            u = u.strip()
            liz = xbmcgui.ListItem(path=u)
            try:
                 html = self.getRequest(suburl)
                 a = json.loads(html)
                 suburl = a['captions'][0]['src']
                 liz.setSubtitles([(suburl)])
            except: pass
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
