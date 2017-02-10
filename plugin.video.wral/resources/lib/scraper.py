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
import sys

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
      shows.append(('/shows/cbs_evening_news/', 'CBS Evening News', self.addonIcon))
      for url, name, thumb in shows:
          name = name.decode(UTF8)
          url = 'http://www.cbs.com%svideo' % url
          infoList = {}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)


  def getAddonEpisodes(self,url,ilist, getFileData = False):
      self.defaultVidStream['width']  = 848
      self.defaultVidStream['height'] = 480
      gcurl = uqp(url)
      if not gcurl.startswith('http'):
          gcurl = 'http://www.cbs.com%s' % gcurl
      html = self.getRequest(gcurl)
      catid = re.compile('video.section_ids = \[(.+?)\]',re.DOTALL).search(html).group(1)
      catid = catid.split(',',1)[0]
      if not catid.isdigit():
          return(ilist)
      ostart = 0
      ototal = 1
      while ostart < ototal:
          html = self.getRequest('http://www.cbs.com/carousels/videosBySection/%s/offset/%s/limit/100/xs/0/' % (catid, str(ostart)))
          vids = json.loads(html)
          ototal = vids['result']['total']
          vids = vids['result']['data']
          for b in vids:
              if b["is_paid_content"] == True:
                  continue
              infoList = {}
              if b.get('airdate_ts') != None:
                  try:
                      infoList['Date'] = datetime.datetime.fromtimestamp(b['airdate_ts']/1000).strftime('%Y-%m-%d')
                      infoList['Aired'] = infoList['Date']
                      infoList['premiered'] = infoList['Date']
                      infoList['Year'] = int(infoList['Aired'].split('-',1)[0])
                  except:
                      pass
              infoList['Title'] = b['episode_title']
              name = infoList['Title']
              url = b['url']
              infoList['Plot'] = b['description']
              thumb = b['thumb'].get("large")
              if thumb == None:
                  thumb = b['thumb'].get("640x480")
              fanart = thumb
              infoList['TVShowTitle'] = b['series_title']
              if b.get('season_number').isdigit():
                  infoList['Season'] = b['season_number']
              if b.get('episode_number').isdigit():
                  infoList['Episode'] = b['episode_number']
              infoList['Studio'] = 'CBS'
              dur = b['duration']
              duration = 0
              dur = dur.strip()
              for d in dur.split(':'):
                  duration = duration*60+int(d)
              infoList['duration'] = duration
              infoList['mediatype'] = 'episode'
              if getFileData == False:
                  ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
              else:
                  ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
          ostart += 100
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name  = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir  = xbmc.translatePath(os.path.join(profile,'TV Shows'))
          movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          ilist = []
          ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
          for season, episode, url in ilist:
              se = 'S%sE%s' % (str(season), str(episode))
              xurl = '%s?mode=GV&url=%s' % (sys.argv[0], url)
              strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
              with open(strmFile, 'w') as outfile:
                  outfile.write(xurl)         
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)



  def getAddonVideo(self,url):
      html = self.getRequest('http://www.cbs.com%s' % uqp(url))
      foundpid = re.compile("cbsplayer.pid = '(.+?)'", re.DOTALL).search(html).group(1)
      headers = self.defaultHeaders.copy()
      headers['User-Agent']= 'Mozilla/5.0 (Linux; U; en-US) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) Version/4.0 Kindle/3.0 (screen 600X800; rotate)'
      pg = self.getRequest('http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&manifest=m3u&mbr=true' % foundpid, None, headers)
      url = re.compile('<video src="(.+?)"', re.DOTALL).search(pg).group(1)
      if url.startswith('http'):
          finalurl = url +'|User-Agent='+urllib.quote(headers['User-Agent'])
      else:
          pg = self.getRequest('http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&mbr=true' % foundpid)
          frtmp,fplay = re.compile('<meta base="(.+?)".+?<video src="(.+?)"',re.DOTALL).search(pg).groups()
          swfurl='http://canstatic.cbs.com/chrome/canplayer.swf swfvfy=true'
          if '.mp4' in fplay:
              pphdr = 'mp4:'
              frtmp = frtmp.replace('&amp;','&')
              fplay = fplay.replace('&amp;','&')
          else:
              pphdr = ''
              frtmp = frtmp.replace('rtmp:','rtmpe:')
              frtmp = frtmp.replace('.net','.net:1935')
              frtmp = frtmp.replace('?auth=','?ovpfv=2.1.9-internal&?auth=')
              swfurl = 'http://vidtech.cbsinteractive.com/player/3_3_2/CBSI_PLAYER_HD.swf swfvfy=true pageUrl=http://www.cbs.com/shows'
          finalurl = '%s playpath=%s%s swfurl=%s timeout=90' % (frtmp, pphdr, fplay, swfurl)
          xbmcgui.Dialog().notification(self.addonName, self.addon.getLocalizedString(30001), self.addonIcon, 5000, False)

      liz = xbmcgui.ListItem(path = finalurl)
      suburl = re.compile('"ClosedCaptionURL" value="(.+?)"',re.DOTALL).search(pg)
      if suburl != None:
          suburl = suburl.group(1)
          if ('xml' in suburl):
              subfile = self.procConvertSubtitles(suburl)
              if subfile != "":
                  liz.setSubtitles([subfile])
      infoList ={}
      infoList['mediatype'] = xbmc.getInfoLabel('ListItem.DBTYPE')
      infoList['Title'] = xbmc.getInfoLabel('ListItem.Title')
      infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
      infoList['Year'] = xbmc.getInfoLabel('ListItem.Year')
      infoList['Premiered'] = xbmc.getInfoLabel('Premiered')
      infoList['Plot'] = xbmc.getInfoLabel('ListItem.Plot')
      infoList['Studio'] = xbmc.getInfoLabel('ListItem.Studio')
      infoList['Genre'] = xbmc.getInfoLabel('ListItem.Genre')
      infoList['Duration'] = xbmc.getInfoLabel('ListItem.Duration')
      infoList['MPAA'] = xbmc.getInfoLabel('ListItem.Mpaa')
      infoList['Aired'] = xbmc.getInfoLabel('ListItem.Aired')
      infoList['Season'] = xbmc.getInfoLabel('ListItem.Season')
      infoList['Episode'] = xbmc.getInfoLabel('ListItem.Episode')
      liz.setInfo('video', infoList)
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
