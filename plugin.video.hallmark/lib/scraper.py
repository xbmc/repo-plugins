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
        addonLanguage  = self.addon.getLocalizedString
        url = 'http://www.hallmarkchanneleverywhere.com/Movies?NodeID=28'
        ilist = self.addMenuItem('Movies','GM', ilist, url, self.addonIcon, self.addonFanart, {} , isFolder=True)
        html = self.getRequest('http://www.hallmarkchanneleverywhere.com/Series?NodeID=29')
        c     = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)">(.+?)<',re.DOTALL).findall(html)
        for  thumb, url, name in c:
              thumb = HALLMARKBASE % thumb
              fanart = thumb
              name = h.unescape(name.decode(UTF8))
              url = HALLMARKBASE % url.replace('&amp;','&')
              html = self.getRequest(url)
              plot = re.compile('<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).group(1)
              plot  = h.unescape(plot.decode(UTF8)).strip()
              infoList ={}
              infoList['Title'] = name
              infoList['Plot']  = plot
              ilist = self.addMenuItem(name,'GE', ilist, url+'|'+name, thumb, fanart, infoList, isFolder=True)
        return(ilist)


  def getAddonEpisodes(self,url,ilist):
        addonLanguage  = self.addon.getLocalizedString
        self.defaultVidStream['width']  = 1280
        self.defaultVidStream['height'] = 720
        url, showName = uqp(url).split('|',1)

        html  = self.getRequest(url)
        c     = re.compile('<div class="commoneptitle".+?<span.+?">(.+?)<.+?"epsynopsis">(.+?)<.+?bc="(.+?)"',re.DOTALL).findall(html)
        for name, plot, vid in c:
              infoList ={}
              infoList['TVShowTitle'] = showName
              infoList['Title'] = h.unescape(name.decode(UTF8))
              infoList['Plot']  = h.unescape(plot.decode(UTF8).strip())
              infoURL = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3811967664001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+vid+'&secureConnections=true&secureHTMLConnections=true'
              html = self.getRequest(infoURL)
              m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
              a = json.loads(html[m.start(1):m.end(1)+1])
              thumb = a['data']['programmedContent']['videoPlayer']['mediaDTO']['videoStillURL']
              fanart = thumb
              url = vid
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        return(ilist)

  def getAddonMovies(self,url,ilist):
        html  = self.getRequest(uqp(url))
        c     = re.compile('<div class="imageviewitem">.+?src="(.+?)".+?class="commontitle" href="(.+?)">(.+?)<.+?fwmediaid = \'(.+?)\'.+?</script>',re.DOTALL).findall(html)
        for  thumb, murl, name, url in c:
              html = self.getRequest(HALLMARKBASE % murl.replace('&amp;','&'))
              genre,mpaa,cast,plot=re.compile('<div class="moviesubtitle">(.+?)<.+?</span>(.+?)<.+?">(.+?)<.+?<div id="imageDetail">.+?</div>(.+?)<', re.DOTALL).search(html).groups()
              genre = genre.strip().replace(';',',')
              mpaa  = mpaa.strip()
              cast  = h.unescape(cast.decode(UTF8))
              cast  = cast.strip().split(';')
              plot  = h.unescape(plot.decode(UTF8)).strip()
              thumb = 'http://www.hallmarkchanneleverywhere.com%s' % thumb
              fanart = thumb
              infoList ={}
              infoList['Title'] = h.unescape(name.decode(UTF8))
              infoList['Genre'] = genre
              infoList['Plot']  = plot
              infoList['MPAA']  = 'TV-'+mpaa
              infoList['Cast']  = cast
              infoList['Studio']  = 'Hallmark Channel'
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
        return(ilist)




  def getAddonVideo(self,url):
    url = 'https://secure.brightcove.com/services/viewer/htmlFederated?&width=859&height=482&flashID=BrightcoveExperience&bgcolor=%23FFFFFF&playerID=3811967664001&playerKey=&isVid=true&isUI=true&dynamicStreaming=true&%40videoPlayer='+url+'&secureConnections=true&secureHTMLConnections=true'

    html = self.getRequest(url)
    m = re.compile('experienceJSON = (.+?)\};',re.DOTALL).search(html)
    a = json.loads(html[m.start(1):m.end(1)+1])
    u =''
    rate = 0
    b = a['data']['programmedContent']['videoPlayer']['mediaDTO']['renditions']
    for c in b:
           if c['encodingRate'] > rate:
              rate = c['encodingRate']
              u = c['defaultURL']

    try:
        suburl = a['data']['programmedContent']['videoPlayer']['mediaDTO']['captions'][0]['URL']
    except:
        suburl = ''

    if (suburl != ''):
      profile = self.addon.getAddonInfo('profile').decode(UTF8)
      subfile = xbmc.translatePath(os.path.join(profile, 'subtitles.srt'))
      prodir  = xbmc.translatePath(os.path.join(profile))
      if not os.path.isdir(prodir):
         os.makedirs(prodir)

      pg = self.getRequest(suburl)
      if pg != "":
        ofile = open(subfile, 'w+')
        captions = re.compile('<p begin="(.+?)" end="(.+?)">(.+?)</p>',re.DOTALL).findall(pg)
        if len(captions) == 0: captions = re.compile("<p .+?begin='(.+?)'.+?end='(.+?)'.+?>(.+?)</p>",re.DOTALL).findall(pg)

        for idx, (cstart, cend, caption) in list(enumerate(captions, start=1)):
          cstart = cstart.replace('.',',')
          cend   = cend.replace('.',',').split('"',1)[0]
          try:
            if '<span' in caption: caption = re.compile('<span.+?>(.+?)</span').search(caption).group(1)
          except: pass
          caption = caption.replace('<br/>','\n')
          try:  caption = h.unescape(caption.encode(UTF8))
          except: pass
          ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
        ofile.close()
      else: suburl = ''


    liz = xbmcgui.ListItem(path = u)
    if suburl != "" : liz.setSubtitles([subfile])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

