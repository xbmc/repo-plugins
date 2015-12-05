# -*- coding: utf-8 -*-
# WCBS Kodi Video Addon
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

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):

     html = self.getRequest('http://www.cbs.com/shows/')
     shows = re.compile('<div class="thumb">.+?href="(.+?)".+?title="(.+?)".+?src="(.+?)".+?</li>', re.DOTALL).findall(html)
     infoList = {}
     fanart = self.addonFanart
     for url, name, thumb in shows:
         url = 'http://www.cbs.com%svideo' % url
         ilist = self.addMenuItem(name.decode(UTF8),'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
        __language__  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 848
        self.defaultVidStream['height'] = 480
        gcurl = uqp(url)
        if not gcurl.startswith('http'): gcurl = 'http://www.cbs.com%s' % gsurl
        html = self.getRequest(gcurl)
        catid = re.compile('video.section_ids = \[(.+?)\]',re.DOTALL).search(html).group(1)
        catid = catid.split(',',1)[0]
        html = self.getRequest('http://www.cbs.com/carousels/videosBySection/%s/offset/0/limit/40/xs/0/' % catid)
        vids = json.loads(html)
        vids = vids['result']['data']
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(self.addonName, __language__(30101))
        pDialog.update(0)
        numShows = len(vids)
        dirty = False
        for i,b in list(enumerate(vids, start=1)):
           if b["is_paid_content"] == True: continue
           print "b = "+str(b)
           infoList = {}
           try:
              infoList['Date']    = datetime.datetime.fromtimestamp(b['airdate_ts']/1000).strftime('%Y-%m-%d')
              infoList['Aired']   = infoList['Date']
              infoList['Year']    = int(infoList['Aired'].split('-',1)[0])
           except: pass
           infoList['Title']   = b['episode_title']
           name                = infoList['Title']
           url                 = b['url']
           infoList['Plot']    = b['description']
           try:    thumb    = b['thumb']["large"]
           except: thumb    = b['thumb']["640x480"]
           fanart = thumb
           infoList['TVShowTitle'] = b['series_title']
           try:    infoList['Season']      = b['season_number']
           except: infoList['Season'] = -1
           try:    infoList['Episode']     = b['episode_number']
           except: infoList['Episode'] = -1
           infoList['Studio']      = 'CBS'
           dur = b['duration']
           duration = 0
           try:
              dur = dur.strip()
              for d in dur.split(':'): duration = duration*60+int(d)
           except: pass
           infoList['duration'] = duration
           try: ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
           except: pass
           pDialog.update(int((100*i)/numShows))
        pDialog.close()
        return(ilist)


  def getAddonVideo(self,url):
      html = self.getRequest('http://www.cbs.com%s' % uqp(url))
      foundpid = re.compile("cbsplayer.pid = '(.+?)'", re.DOTALL).search(html).group(1)
      pg = self.getRequest('http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&mbr=true' % foundpid)
      subfile = ""
      try:
          suburl = re.compile('"ClosedCaptionURL" value="(.+?)"',re.DOTALL).search(pg).group(1)
      except:
          suburl = ""

      frtmp,fplay = re.compile('<meta base="(.+?)".+?<video src="(.+?)"',re.DOTALL).search(pg).groups()
      swfurl='http://canstatic.cbs.com/chrome/canplayer.swf swfvfy=true'
      if '.mp4' in fplay:
          pphdr = 'mp4:'
          frtmp = frtmp.replace('&amp;','&')
          fplay = fplay.replace('&amp;','&')
      else:
          pphdr = ''
          xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( __addonname__,__language__(30011) , '10000') ) #added
          frtmp = frtmp.replace('rtmp:','rtmpe:')
          frtmp = frtmp.replace('.net','.net:1935')
          frtmp = frtmp.replace('?auth=','?ovpfv=2.1.9-internal&?auth=')
          swfurl = 'http://vidtech.cbsinteractive.com/player/3_3_2/CBSI_PLAYER_HD.swf swfvfy=true pageUrl=http://www.cbs.com/shows'
      finalurl = '%s playpath=%s%s swfurl=%s timeout=20' % (frtmp, pphdr, fplay, swfurl)
      liz = xbmcgui.ListItem(path = finalurl)

      if (suburl != "") and ('xml' in suburl):
         profile = self.addon.getAddonInfo('profile').decode(UTF8)
         subfile = xbmc.translatePath(os.path.join(profile, 'subtitles.srt'))
         prodir  = xbmc.translatePath(os.path.join(profile))
         if not os.path.isdir(prodir):
            os.makedirs(prodir)

         pg = self.getRequest(suburl)
         if pg != "":
            ofile = open(subfile, 'w+')
            captions = re.compile('<p begin="(.+?)" end="(.+?)"(.+?)/p>',re.DOTALL).findall(pg)
            for idx, (cstart, cend, caption) in list(enumerate(captions, start=1)):
                cstart = cstart.replace('.',',')
                cend   = cend.replace('.',',').split('"',1)[0]
                caption = caption.replace('<br/>','\n').replace('<br></br>','\n').replace('&apos;',"'")
                pieces  = re.compile('>(.+?)<', re.DOTALL).findall(caption)
                if len(pieces) > 0 :
                  caption = ''
                  for piece in pieces: caption = caption + piece
                caption = caption.strip() 
                try:    caption = h.unescape(caption)
                except: pass
                ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
            ofile.close()

      if subfile != "" : liz.setSubtitles([subfile])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)


# Start of Module

addonName = re.search('plugin\://plugin.video.(.+?)/',str(sys.argv[0])).group(1)
ma = myAddon(addonName)
ma.processAddonEvent()
del myAddon

