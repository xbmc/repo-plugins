# -*- coding: utf-8 -*-
# Test 7 KodiAddon (tubitv)
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

h = HTMLParser.HTMLParser()
uqp = urllib.unquote_plus
UTF8 = 'utf-8'


class myAddon(t1mAddon):

 def getAddonMenu(self,url,ilist):

   infoList = {}
   html  = self.getRequest('http://tubitv.com')
   shows = re.compile('<li.+?class=".+?href="(.+?)">(.+?)<',re.DOTALL).findall(html)
   for url, name in shows:
      ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
   return(ilist)

 def getExtraMeta(self, url, infoList):
          html = self.getRequest('http://tubitv.com%s' % url)
          m = re.compile("class='video-info-container'(.+?)<DIV class='share-row'", re.DOTALL).search(html)
          try:    infoList['Plot']  = re.compile("itemprop='description'>(.+?)<", re.DOTALL).search(html,m.start(1), m.end(1)).group(1)
          except: pass
          try:
                  md = re.compile("class='video-metadata'>(.+?)<", re.DOTALL).search(html,m.start(1), m.end(1)).group(1)
                  year = int(md[0:4])
                  if year > 1900:
                     infoList['Year']  = year
                     md = md[4:]
                  md=md.strip()
                  md = md.split('\t',1)
                  infoList['MPAA'] = md[1].strip()
                  dur  = md[0].strip()
                  dur  = dur.split(':')
                  duration = 0
                  for t in dur: duration = duration*60+int(t)
                  infoList['duration'] = duration
          except: pass
          try:    infoList['director'] = re.compile('>Directed by (.+?)<', re.DOTALL).search(html,m.start(1), m.end(1)).group(1)
          except: pass
          try:    
                  cast = re.compile('>Starring (.+?)<', re.DOTALL).search(html,m.start(1), m.end(1)).group(1)
                  infoList['cast'] = cast.split(',')
          except: pass
          try:
                  genres = re.compile("class='video-categories'>(.+?)<", re.DOTALL).search(html,m.start(1), m.end(1)).group(1)
                  infoList['genre'] = genres.replace('\t','').replace(' ','')
          except: pass
          return  infoList

 def getAddonShows(self,url,ilist):
   url   = uqp(url)
   meta = self.getAddonMeta()
   try:    i = len(meta)
   except: meta={}
   html  = self.getRequest('http://tubitv.com%s' % url)
   shows = re.compile("<A class=.+?href='(.+?)'.+?src='(.+?)'.+?title'>(.+?)<.+?description'>(.+?)<.+?</A",re.DOTALL).findall(html)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   numShows = len(shows)
   dirty = False
   for i,(url,img,name,plot) in list(enumerate(shows, start=1)):
     fanart = img.rsplit('_',1)[0]+'_11.png'
     try:
       (name, img, infoList, vtype) = meta[url]
       if vtype == 'tvshow':  ilist = self.addMenuItem(name,'GE', ilist, url+'|'+name, img, fanart, infoList, isFolder=True)
       elif vtype == 'movie': ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
     except:
       infoList = {}
       try: 
           season, epi = re.compile('S([0-9]*)\:E([0-9]*)').search(url).groups()
           name = name+' (Series)'
           infoList['Title'] = name
           infoList['Plot']  = plot
           ilist = self.addMenuItem(name,'GE', ilist, url+'|'+name, img, fanart, infoList, isFolder=True)
           meta[url] = (name, img, infoList, 'tvshow')
           dirty = True
       except:
           infoList['Title']         = name
           infoList = self.getExtraMeta(url, infoList)
           ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
           meta[url] = (name, img, infoList, 'movie')
           dirty = True
     pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)


 def getAddonEpisodes(self,url,ilist):
   url   = uqp(url)
   gsurl, sname = url.split('|',1)
   gsurl = gsurl.strip('.')
   meta = self.getAddonMeta()
   try:    i = len(meta[sname])
   except: meta[sname]={}
   html  = self.getRequest('http://tubitv.com%s' % gsurl)
   epis  = re.compile("<A class='img_box' href='(.+?)'.+?src='(.+?)'.+?Title'>(.+?)<.+?</A", re.DOTALL).findall(html)
   numShows = len(epis)
   pDialog = xbmcgui.DialogProgress()
   pDialog.create(self.addonName, self.localLang(30101))
   pDialog.update(0)
   dirty = False
   for i,(url,img,name) in list(enumerate(epis, start=1)):
     try:
          (name, img, infoList, vtype) = meta[sname][url] 
     except:
          infoList={}
          infoList['TVShowTitle']   = sname
          try:
               season, episode = re.compile('S(..)\:E(..) ').search(name).groups()
               title = name.split(':',1)[1].split(' ',1)[1].strip(' \t-')
          except: season, episode, title = [0, 0, name]
          name = title  
          infoList['Title']         = title
          infoList['Season']        = season
          infoList['Episode']       = episode
          infoList = self.getExtraMeta(url, infoList)

     fanart = img.rsplit('_',1)[0]+'_11.png'
     ilist = self.addMenuItem(name,'GV', ilist, url, img, fanart, infoList, isFolder=False)
     meta[sname][url] = (name, img, infoList, 'episode')
     dirty = True
     pDialog.update(int((100*i)/numShows))
   pDialog.close()
   if dirty == True: self.updateAddonMeta(meta)
   return(ilist)


 def getAddonVideo(self,lurl):
     token = self.addon.getSetting('token')

     if token != '':
        yheaders = self.defaultHeaders.copy()
        yheaders["Accept"] = "text/html,application/xhtml+xml,application/xml,*/*"
        yheaders["Cookie"] = token
        url = ('http://tubitv.com%s' % (uqp(lurl).replace('./','/')))
        html = self.getRequest(url, None, yheaders)
        try:    a = re.compile("<script>apu='(.+?)'",re.DOTALL).search(html).group(1)
        except: token = ''

     if token == '':
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)
        username = self.addon.getSetting('login_name')
        password = self.addon.getSetting('login_pass')
        url1  = ('http://tubitv.com/login')
        xheaders = self.defaultHeaders.copy()
        xheaders["Referer"]      = "http://tubitv.com/"
        xheaders["Connection"]   = "keep-alive"
        xheaders["Accept"]       = "text/html,application/xhtml+xml,application/xml,*/*"
        xheaders["Content-Type"] = "application/x-www-form-urlencoded"
        udata = 'username=%s&password=%s' % (urllib.quote(username),urllib.quote(password))
        html = self.getRequest(url1, udata, xheaders)
        token = str(cj).split(' ')[1]
        token = token+';'
        self.addon.setSetting('token', token)
        url = ('http://tubitv.com%s' % (uqp(lurl).replace('./','/')))
        html = self.getRequest(url)

        try: a = re.compile("<script>apu='(.+?)'",re.DOTALL).search(html).group(1)
        except:
            xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( self.addonName, self.localLang(30018) , 5000) )
            return


     a = list(a)
     for x in range(len(a)):
             if a[x] == '_':
                a[x] = '_'
             elif ord(a[x]) >= ord('n'):
                a[x] = chr(ord(a[x])-(ord('n'))+(ord('a')))
             elif ord(a[x])>=ord('a'): 
                a[x] = chr(ord(a[x]) - ord('a')+ord('n'))
             elif ord(a[x]) >= ord('N'):
                a[x] = chr(ord(a[x])-(ord('N'))+(ord('A')))
             elif ord(a[x])>=ord('A'): 
                a[x] = chr(ord(a[x]) - ord('A')+ord('N'))

             x += 1
     a = ''.join(a)
     u = a[::-1] # this reverses the string
     u = u.replace('./','/')


     liz = xbmcgui.ListItem(path=u)

     suburl = re.compile("sbt=(.+?);", re.DOTALL).search(html).group(1)
     if suburl != "undefined":
          suburl = json.loads(suburl)
          subs = []
          for sub in suburl:
             subs.append(sub["subtitle"]["url"])
          liz.setSubtitles(subs)
     xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon
