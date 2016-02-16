# -*- coding: utf-8 -*-
# ABCFamily Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import datetime
import urllib
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
     meta = self.getAddonMeta()
     try:    i = len(meta['shows'])
     except: meta['shows']={}
     html = self.getRequest('http://abcfamily.go.com/shows')
     a = re.compile('<article class="item fepAvailable">.+?href="(.+?)".+?title="(.+?)".+?"src":"(.+?)".+?"description hidden">(.+?)<.+?</article',re.DOTALL).findall(html)
     for url, name, img1, plot in a:
              name = name.replace('<strong>','').replace('</strong>','')
              name=h.unescape(name.decode(UTF8))
              fanart = 'http://static.east.abc.go.com/service/image/index/id/%s/dim/640x360.png' % img1
              thumb = fanart
              infoList ={}
              infoList['Title'] = name
              infoList['TVShowTitle'] = name
              infoList['Plot'] = h.unescape(plot.decode(UTF8))
              meta['shows'][url] = (name, infoList)
              ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     self.updateAddonMeta(meta)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        __language__  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 1920
        self.defaultVidStream['height'] = 1080
        gcurl = uqp(url)
        meta  = self.getAddonMeta()
        sname = gcurl
        try:  i = len(meta[sname])
        except:
              meta[sname]={}
        html = self.getRequest(gcurl)
        vids = re.compile('<article class="item fep available">.+?href="(.+?)".+?</article>', re.DOTALL).findall(html)
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(self.addonName, __language__(30101))
        pDialog.update(0)
        numShows = len(vids)
        dirty = False
        for i,xurl in list(enumerate(vids, start=1)):
           try:
               (name, vd, url, thumb, fanart, infoList) = meta[sname][xurl]
           except:
               dirty = True
               html = self.getRequest(xurl)
               try:    vd = re.compile('vp:video="VDKA(.+?)"',re.DOTALL).search(html).group(1)
               except: 
                 try: 
                     vd = re.compile('data-video-id="VDKA(.+?)"',re.DOTALL).search(html).group(1)
                 except: continue

               url = 'http://cdnapi.kaltura.com//api_v3/index.php?service=multirequest&action=null&ignoreNull=1&2%3Aaction=getContextData&3%3Aaction=list&2%3AcontextDataParams%3AflavorTags=uplynk&2%3AentryId='+vd+'&apiVersion=3%2E1%2E5&1%3Aversion=-1&2%3AcontextDataParams%3AstreamerType=http&3%3Afilter%3AentryIdEqual='+vd+'&clientTag=kdp%3Av3%2E9%2E2&1%3AentryId='+vd+'&2%3AcontextDataParams%3AobjectType=KalturaEntryContextDataParams&3%3Afilter%3AobjectType=KalturaCuePointFilter&2%3Aservice=baseentry&1%3Aservice=baseentry&1%3Aaction=get'
               html = self.getRequest(url)
               url,duration,name, description, catname,thumb,sdate = re.compile('<dataUrl>(.+?)</dataUrl>.+?<duration>(.+?)</duration>.+?<name>(.+?)</name><description>(.+?)</description>.+?<categories>(.+?)</categories>.+?<thumbnailUrl>(.+?)</thumbnailUrl>.+?<startDate>(.+?)</startDate>',re.DOTALL).search(html).groups()
               name = name.decode(UTF8)
               name = h.unescape(name)
               plot = h.unescape(description.decode(UTF8))
               url = url.strip()
               try: url = 'http://cdnapi.kaltura.com/p/585231/sp/58523100/playManifest/entryId/%s/flavorId/%s/format/http/protocol/http/cdnHost/cdnbakmi.kaltura.com/storageId/1571/uiConfId/8628162/tags/uplynk/a/a.f4m' % (vd , re.compile('<entryId>(.+?)<',re.DOTALL).search(html).group(1))
               except: pass
               thumb = thumb.strip()
               fanart = thumb
               infoList = {}
               try:
                 x = name.split(' ',3)
                 if x[1].startswith('Ep'):
                   infoList['Season'] = int(x[0].replace('S',''))
                   infoList['Episode'] = int(x[2])
                   name = x[3]
                 else: raise ValueError('Non fatal error')
               except:
                   infoList['Season'] = 0
                   infoList['Episode'] = 0
               infoList['Title'] = name
               infoList['Plot']  = plot
               infoList['TVShowTitle'] = h.unescape(catname)
               infoList['Duration'] = int(duration)
               infoList['Date']     = datetime.datetime.fromtimestamp(int(sdate)).strftime('%Y-%m-%d')
               infoList['Aired']    = infoList['Date']
               infoList['Year']     = int(infoList['Aired'].split('-',1)[0])
               infoList['Studio']   = 'ABC'
               meta[sname][xurl] = (name, vd, url, thumb, fanart, infoList)
           try: ilist = self.addMenuItem(name,'GV', ilist, url+'|'+vd, thumb, fanart, infoList, isFolder=False)
           except: pass
           pDialog.update(int((100*i)/numShows))
        pDialog.close()
        if dirty == True: self.updateAddonMeta(meta)
        return(ilist)


  def getAddonVideo(self,url):
    finalurl = uqp(url)
    finalurl, vid = finalurl.split('|',1)
    if finalurl.endswith('.f4m'):
       html = self.getRequest(finalurl)
       finalurl = re.compile('<media url="(.+?)"',re.DOTALL).search(html).group(1).replace('&amp;','&')
    liz = xbmcgui.ListItem(path = finalurl)

    subfile = ""
    suburl = 'http://api.contents.watchabc.go.com/vp2/ws/s/contents/2020/videos/002/001/-1/-1/-1/VDKA%s/-1/-1?v=08.00' % vid
    if (suburl != ""):
       profile = self.addon.getAddonInfo('profile').decode(UTF8)
       prodir  = xbmc.translatePath(os.path.join(profile))
       if not os.path.isdir(prodir):
          os.makedirs(prodir)

       pg = self.getRequest(suburl)
       suburl = re.compile('<closedcaption enabled="true">.+?http:(.+?)<',re.DOTALL).search(pg).group(1)
       suburl = 'http:'+suburl.strip()
       pg = self.getRequest(suburl)

       if pg != "":
          subfile = xbmc.translatePath(os.path.join(profile, 'Subtitles.srt'))
          ofile = open(subfile, 'w+')
          captions = re.compile('<p begin="(.+?)" end="(.+?)".+?/>(.+?)</p>',re.DOTALL).findall(pg)
          for idx, (cstart, cend, caption) in list(enumerate(captions, start=1)):
              if cstart.startswith('01'): cstart = cstart.replace('01','00',1)
              if cend.startswith('01'): cend = cend.replace('01','00',1)
              cstart = cstart.replace('.',',')
              cend   = cend.replace('.',',').split('"',1)[0]
              caption = caption.replace('<br/>','\n')
              try:  caption = h.unescape(caption.encode(UTF8))
              except: pass
              ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
          ofile.close()
    if subfile != "" : liz.setSubtitles([subfile])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

