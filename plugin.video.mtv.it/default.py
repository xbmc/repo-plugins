#!/usr/bin/python
import sys, xbmcplugin, xbmcgui#, datetime
from neverwise import Util
#from operator import itemgetter


class MTV(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    # Programmi.
    if len(self._params) == 0:
      shows = self._getMTVResponse('/serie-tv')
      if shows.isSucceeded:
        shows = shows.body.findAll('h3', 'showpass')
        for show in shows:
          name = show.nextSibling.strong.text
          img = show.img['data-original']
          index = img.rfind('?')
          show.nextSibling.strong.extract()
          li = Util.createListItem(name, thumbnailImage = img[:index], streamtype = 'video', infolabels = { 'title' : name, 'plot' : show.nextSibling.text })
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 's', 'path' : show.a['href'] }), li, True)
        xbmcplugin.endOfDirectory(self._handle)

    # Stagioni.
    elif self._params['action'] == 's':
      response = self._getMTVResponse(self._params['path'])
      if response.isSucceeded:
        if response.body.renderContents().find('<h2>Troppo tardi! <b>&#9787;</b></h2>') == -1:
          seasons = response.body.find('ul', 'nav').findAll('a')
          if xbmcplugin.getSetting(self._handle, 'show_seasons') == 'false' or len(seasons) > 1:
            title = response.body.find('h1', { 'itemprop' : 'name' }).text
            for season in seasons:
              link = season['href']
              season = season.text
              li = Util.createListItem(season, streamtype = 'video', infolabels = { 'title' : season, 'plot' : '{0} di {1}'.format(season, title) })
              xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 'p', 'path' : link }), li, True)
            xbmcplugin.endOfDirectory(self._handle)
          else:
            self._getEpisodes(seasons[0]['href'])
        else:
          xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30000)) # Troppo tardi! I diritti di questo video sono scaduti.

    # Puntate.
    elif self._params['action'] == 'p':
      self._getEpisodes(self._params['path'])

    # Risoluzioni.
    elif self._params['action'] == 'r':
      videoId = Util.getResponseBS(self._params['path'])
      if videoId.isSucceeded:
        videoId = videoId.body.find('div', 'MTVNPlayer')
        if videoId != None:
          qlySetting = xbmcplugin.getSetting(self._handle, 'vid_quality')
          if qlySetting == '0':
            qlySetting = 180
          elif qlySetting == '1':
            qlySetting = 270
          elif qlySetting == '2':
            qlySetting = 360
          elif qlySetting == '3':
            qlySetting = 432
          elif qlySetting == '4':
            qlySetting = 576
          elif qlySetting == '5':
            qlySetting = 720
          elif qlySetting == '6':
            qlySetting = 1080
          videoId = videoId['data-contenturi']
          response = Util.getResponseBS('http://intl.esperanto.mtvi.com/www/xml/media/mediaGen.jhtml?uri=mgid:uma:video:mtv.it{0}'.format(videoId[videoId.rfind(':'):]))
          if response.isSucceeded:
            response = response.body.findAll('rendition')
            streams = []
            for stream in response:
              streams.append(( abs(qlySetting - int(stream['height'])), stream.src.text ))
            streams = sorted(streams, key = lambda stream: stream[0])
            Util.playStream(self._handle, '', path = streams[0][1])
            #for duration, bitrate, url in streams:
            #  title = Util.getTranslation(idLabel)
            #  idLabel += 1
            #  li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title }, duration = duration)
            #  xbmcplugin.addDirectoryItem(self._handle, '{0} swfUrl=http://media.mtvnservices.com/player/prime/mediaplayerprime.2.3.7.swf?uri={1}.swf swfVfy=true'.format(url, self._params['path']), li, False)
            #xbmcplugin.endOfDirectory(self._handle)
        else:
          xbmcgui.Dialog().ok(Util._addonName, Util.showVideoNotAvailableDialog()) # Video non disponibile.


  def _getMTVResponse(self, link):
    return Util.getResponseBS('http://ondemand.mtv.it{0}'.format(link))


  def _getEpisodes(self, path):
    index = path.rfind('/')
    videos = self._getMTVResponse('{0}.rss'.format(path[:index]))
    if videos.isSucceeded:
      videos = videos.body.findAll('item')
      season = '{0}/'.format(path[index:])
      for video in videos:
        if video.link.nextSibling.find(season) > -1:
          name = video.title.text
          img = video.enclosure['url']
          iResEnd = img.rfind('.')
          iResStart = iResEnd - 3
          if img[iResStart:iResEnd] == '140':
            img = '{0}640{1}'.format(img[:iResStart], img[iResEnd:])
          li = Util.createListItem(name, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : name, 'plot' : video.description.text }, isPlayable = True)
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 'r', 'path' : video.link.nextSibling }), li)
      xbmcplugin.endOfDirectory(self._handle)


# Entry point.
#startTime = datetime.datetime.now()
mtv = MTV()
del mtv
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
