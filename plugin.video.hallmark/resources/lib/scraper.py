# -*- coding: utf-8 -*-
# Hallmark Channel Kodi Video Addon
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
HALLMARKBASE  = 'http://www.hallmarkchanneleverywhere.com%s'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      url = 'http://www.hallmarkchanneleverywhere.com/Movies?NodeID=28'
      ilist = self.addMenuItem('Movies','GM', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
      html = self.getRequest('http://www.hallmarkchanneleverywhere.com/Series?NodeID=29')
      c = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)">(.+?)<',re.DOTALL).findall(html)
      for thumb, url, name in c:
          thumb = HALLMARKBASE % thumb
          fanart = thumb
          name = h.unescape(name.decode(UTF8))
          url = HALLMARKBASE % url.replace('&amp;','&')
          html = self.getRequest(url)
          plot = re.compile('<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).group(1)
          plot  = h.unescape(plot.decode(UTF8)).strip()
          infoList ={}
          infoList['Title'] = name
          infoList['TVShowTitle'] = name
          infoList['Plot']  = plot
          infoList['mediatype'] = 'tvshow'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AL%s)' % (sys.argv[0], qp(url)))]
          ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True, cm=contextMenu)
      return(ilist)

  def getAddonEpisodes(self,url,ilist, getFileData = False):
      self.defaultVidStream['width']  = 1280
      self.defaultVidStream['height'] = 720
      html = self.getRequest(url)
      c = re.compile('<div class="commoneptitle".+?<span.+?">(.+?)<.+?Season (.+?) .+?Episode (.+?)\n.+?"epsynopsis">(.+?)<.+?bccode.+?href="(.+?)"',re.DOTALL).findall(html)
      for name, season, episode, plot, vid in c:
          infoList ={}
          infoList['TVShowTitle'] = xbmc.getInfoLabel('ListItem.TVShowTitle')
          infoList['Title'] = h.unescape(name.decode(UTF8))
          infoList['Plot']  = h.unescape(plot.decode(UTF8).strip())
          infoList['Episode'] = int(episode)
          infoList['Season'] = int(season)
          infoList['Studio'] = 'Hallmark'
          infoList['mediatype'] = 'episode'
          thumb = self.addonIcon
          fanart = self.addonFanart
          url = HALLMARKBASE % vid
          if getFileData == False:
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
          else:
              ilist.append((infoList.get('Season',''), infoList.get('Episode',''), url))
      return(ilist)

  def getAddonMovies(self,url,ilist):
      html = self.getRequest(uqp(url))
      c = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)".+?">(.+?)<.+?fwmediaid = \'(.+?)\'.+?</script>',re.DOTALL).findall(html)
      for thumb, murl, name, url in c:
          url = HALLMARKBASE % murl.replace('&amp;','&')
          html = self.getRequest(url)
          genre,mpaa,cast,plot=re.compile('<div class="moviesubtitle">(.+?)<.+?</span>(.+?)<.+?">(.+?)<.+?<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).groups()
          genre = genre.strip().replace(';',',')
          mpaa = mpaa.strip()
          cast = h.unescape(cast.decode(UTF8))
          cast = cast.strip().split(';')
          plot = h.unescape(plot.decode(UTF8)).strip()
          thumb = 'http://www.hallmarkchanneleverywhere.com%s' % thumb
          fanart = thumb
          infoList ={}
          infoList['Title'] = h.unescape(name.decode(UTF8))
          infoList['Genre'] = genre
          infoList['Plot'] = plot
          infoList['MPAA'] = 'TV-'+mpaa
          infoList['Cast'] = cast
          infoList['Studio'] = 'Hallmark'
          infoList['mediatype'] = 'movie'
          contextMenu = [('Add To Library','XBMC.RunPlugin(%s?mode=DF&url=AM%s)' % (sys.argv[0], url))]
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False, cm=contextMenu)
      return(ilist)

  def doFunction(self, url):
      func = url[0:2]
      url  = url[2:]
      if func == 'AL':
          name = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir = xbmc.translatePath(os.path.join(profile,'TV Shows'))
          movieDir = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          ilist = []
          ilist = self.getAddonEpisodes(url, ilist, getFileData = True)
          for season, episode, url in ilist:
              se = 'S%sE%s' % (str(season), str(episode))
              xurl = '%s?mode=GV&url=%s' % (sys.argv[0], qp(url))
              strmFile = xbmc.translatePath(os.path.join(movieDir, se+'.strm'))
              with open(strmFile, 'w') as outfile:
                  outfile.write(xurl)         
      elif func == 'AM':
          name  = xbmc.getInfoLabel('ListItem.Title')
          profile = self.addon.getAddonInfo('profile').decode(UTF8)
          moviesDir  = xbmc.translatePath(os.path.join(profile,'Movies'))
          movieDir  = xbmc.translatePath(os.path.join(moviesDir, name))
          if not os.path.isdir(movieDir):
              os.makedirs(movieDir)
          strmFile = xbmc.translatePath(os.path.join(movieDir, name+'.strm'))
          with open(strmFile, 'w') as outfile:
              outfile.write('%s?mode=GV&url=%s' %(sys.argv[0], url))
      json_cmd = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan", "params": {"directory":"%s/"},"id":1}' % movieDir.replace('\\','/')
      jsonRespond = xbmc.executeJSONRPC(json_cmd)

  def getAddonVideo(self,url):
      html = self.getRequest(url)
      u = re.compile("videourl = '(.+?)'", re.DOTALL).search(html).group(1)
      suburl = re.compile('captionsrc = (.+?);', re.DOTALL).search(html)
      if not (suburl is None):
          suburl = suburl.group(1)
          suburl = eval(suburl)
          subfile = HALLMARKBASE % suburl.replace('.xml','.vtt')
      else:
          subfile = ''
      liz = xbmcgui.ListItem(path = u)
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
