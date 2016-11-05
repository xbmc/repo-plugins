# -*- coding: utf-8 -*-
# KodiAddon (MeTV)
#
from t1mlib import t1mAddon
import json
import re
import urllib
import xbmcplugin
import xbmcgui
import HTMLParser
import sys

h = HTMLParser.HTMLParser()
qp  = urllib.quote_plus
uqp = urllib.unquote_plus
UTF8     = 'utf-8'
METVBASE = 'http://metvnetwork.com%s'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
     meta = self.getAddonMeta()
     try:    i = len(meta['shows'])
     except: meta['shows']={}

     addonLanguage  = self.addon.getLocalizedString
     name = addonLanguage(30101)
     name = addonLanguage(30102)
     ilist.append(('%s?url=%s&name=%s&mode=GE' % (sys.argv[0],qp('/videos/classic-commercials'),qp(name)),xbmcgui.ListItem(name,'',self.addonIcon, None), True))
     name = addonLanguage(30103)
     ilist.append(('%s?url=%s&name=%s&mode=GE' % (sys.argv[0],qp('/videos/public-domain-classics'),qp(name)),xbmcgui.ListItem(name,'',self.addonIcon, None), True))

     pg = self.getRequest(METVBASE % '/videos/')
     shows = re.compile('<div class="content-grid-item video-grid-item.+?href="(.+?)".+?src="(.+?)".+?">(.+?)<.+?</div>',re.DOTALL).findall(pg)
     fanart = self.addonFanart
     for url, thumb, name in shows:
       try:
         (name, infoList) = meta['shows'][url]
       except:
         pg = self.getRequest(METVBASE % url.rsplit('/',1)[0])
         try:
           plot = re.compile('<div class="show-synopsis has-airings">(.+?)</div',re.DOTALL).search(pg).group(1).strip()
         except:
           try:    plot = re.compile('<div class="show-synopsis">(.+?)</div',re.DOTALL).search(pg).group(1).strip()
           except: plot = ''
         name = name.strip()
         infoList = {}
         infoList['MPAA']        = ''
         infoList['TVShowTitle'] = name
         infoList['Title']       = name
         infoList['Studio']      = addonLanguage(30100)
         infoList['Plot'] = h.unescape(plot.decode(UTF8))
         meta['shows'][url] = (name, infoList)
       ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
     self.updateAddonMeta(meta)
     return(ilist)


  def getAddonEpisodes(self,url,ilist):
    addonLanguage  = self.addon.getLocalizedString
    self.defaultVidStream['width'] = 720
    self.defaultVidStream['height']= 480
    pg = self.getRequest(METVBASE % url)
    try:     showName = re.compile('<div class="show-header".+?<h1>(.+?)</h1>',re.DOTALL).search(pg).group(1)
    except:  showName = addonLanguage(30100)
    try:     fanart = re.compile('<img class="show-banner" src="(.+?)"',re.DOTALL).search(pg).group(1)
    except:  fanart = self.addonFanart
    m = re.compile('<div id="main-content">(.+?)main-content ',re.DOTALL).search(pg)
    try:      x = len(m.group(1))
    except:   m = re.compile('<div id="main-content">(.+?)<a href="/video/#">',re.DOTALL).search(pg)
    episodes = re.compile('<div class="category-list-item clearfix">.+?href="(.+?)".+?img src="(.+?)".+?href=.+?>(.+?)<.+?</div>(.+?)<div class="content-meta content-meta-tags">',re.DOTALL).findall(pg,m.start(1),m.end(1))
    for showpage, thumb, name, plot in episodes:
      plot = plot.replace('</span>','').strip()
      try:
         url = re.compile('/media/(.+?)/').search(thumb).group(1)
      except:
         url = 'BADASS'+showpage
      infoList = {}
      infoList['MPAA']        = ''
      infoList['TVShowTitle'] = showName
      infoList['Title']       = name
      infoList['Studio']      = addonLanguage(30100)
      infoList['Genre']       = ''
      infoList['Season']      = 0
      infoList['Episode']     = -1
      infoList['Plot']        = h.unescape(plot)
      ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
    return(ilist)

  def getUrl(self,mediaID):
     headers = self.defaultHeaders
     headers['Host']='production-ps.lvp.llnw.net'
     html = self.getRequest('http://production-ps.lvp.llnw.net/r/PlaylistService/media/%s/getPlaylistByMediaId' % mediaID, None, headers)
     a = json.loads(html)
     show_url=''
     highbitrate = float(0)
     for stream in a['playlistItems'][0]['streams']:
         bitrate = float(stream['videoBitRate'])
         if bitrate > highbitrate:
            show_url = stream['url']
            highbitrate = float(bitrate)
     show_url  = show_url.split('mp4:',1)[1]
     finalurl  = 'http://s2.cpl.delvenetworks.com/%s' % show_url
     return finalurl



  def getAddonVideo(self,url):
    subfile = ""
    mediaID = uqp(url)
    if mediaID.startswith('BADASS'):
        mediaID = METVBASE % mediaID.replace('BADASS','')
        pg = self.getRequest(mediaID)
        if 'USE_YOUTUBE = true' in pg: return
        try: mediaID = re.compile('currentVideoID = "(.+?)"',re.DOTALL).search(pg).group(1)
        except: return

    url = mediaID
    liz = xbmcgui.ListItem(path = self.getUrl(url))

    try:
           headers = self.defaultHeaders
           headers['Host']='api.video.limelight.com'

           html = self.getRequest('http://api.video.limelight.com/rest/organizations/abee2d5fad8944c790db6a0bfd3b9ebd/media/%s/properties.json' % url, None, headers)
           a = json.loads(html)
           try: 
               subfile = a["captions"][0]["url"]
           except:
               pass
    except:
           pass

    if subfile != "" : liz.setSubtitles([subfile])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
