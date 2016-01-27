#!/usr/bin/python
import re, sys, xbmcplugin, xbmcgui#, datetime
from neverwise import Util


class LaCosa(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    if len(self._params) == 0: # Visualizzazione del menu.

      # Diretta.
      #live = self._getLaCosaResponse('')
      #if live != None:
      #  phpPage = live.find('div', 'box_bottom').script['src']
      #  img = live.find('img', 'logo')['src']
      #  live = Util.getHtml(phpPage).renderContents()
      #  if live != None:
      #    url = '{0}.m3u8'.format(re.compile('file: "(.+?)\.m3u8"').findall(live)[0])
      #    li = Util.createListItem(Util.getTranslation(30000), thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : Util._addonName }, isPlayable = True) # Diretta.
      #    xbmcplugin.addDirectoryItem(self._handle, url, li, False)

      # Shows.
      shows = self._getLaCosaResponse('/rubriche')
      if shows.isSucceeded:
        shows = shows.body.findAll('div', 'icon_programmi')
        for show in shows:
          title = show.h3.a.text
          li = Util.createListItem(title, thumbnailImage = show.img['src'], streamtype = 'video', infolabels = { 'title' : title, 'plot' : show.p.text })
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 's', 'page' : show.a['href'] }), li, True)

      #if (live == None or not live) and (shows == None or not shows): # Se sono vuoti oppure liste vuote.
      #  Util.showConnectionErrorDialog() # Errore connessione internet!
      #elif live == None or not live:
      #  xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30001)) # Errore recupero stream diretta.
      #el
      if shows == None or not shows:
        xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30002)) # Errore recupero shows.

      # Show items.
      #if live != None or shows != None:
      if shows != None:
        xbmcplugin.endOfDirectory(self._handle)

    else:

      response = Util.getResponseBS(self._params['page'])
      if response.isSucceeded:

        # Videos.
        if self._params['id'] == 's': # Visualizzazione video di uno show.
          videos = response.body.find('div', id='recenti_canale').findAll('li')
          for video in videos:
            title = video.h4.text
            time = video.find('span', 'videoTime')
            if time != None:
              time = time.text.split(':')
              if len(time) == 1:
                time = time[0].split('.')
              if len(time) == 3:
                time = (int(time[0]) * 3600) + (int(time[1]) * 60) + int(time[2])
              else:
                time = (int(time[0]) * 60) + int(time[1])
            li = Util.createListItem(title, thumbnailImage = video.img['src'], streamtype = 'video', infolabels = { 'title' : title }, duration = time, isPlayable = True)
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : video.a['href'] }), li, False)

          if len(videos) > 0:
            xbmcplugin.endOfDirectory(self._handle)
          else:
            xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30003)) # Errore recupero video shows.

        # Play video.
        elif self._params['id'] == 'v':
          title = response.body.find('meta', { 'property' : 'og:title' })['content']
          img = response.body.find('meta', { 'property' : 'og:image' })['content']
          descr = response.body.find('meta', { 'property' : 'og:description' })['content']
          streams = re.findall("',file: '(.+?)'", response.body.renderContents())
          try:
            Util.playStream(self._handle, title, img, streams[0], 'video', { 'title' : title, 'plot' : descr })
          except:
            Util.playStream(self._handle, title, img, streams[1], 'video', { 'title' : title, 'plot' : descr })


  def _getLaCosaResponse(self, link):
    return Util.getResponseBS('http://www.beppegrillo.it/la_cosa{0}'.format(link))


# Entry point.
#startTime = datetime.datetime.now()
lc = LaCosa()
del lc
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
