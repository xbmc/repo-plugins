#!/usr/bin/python
import re, sys, xbmcplugin, xbmcgui#, datetime
from neverwise import Util
from operator import itemgetter


class MTV(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    # Programmi.
    if len(self._params) == 0:
      shows = self._getMTVResponse('/serie-tv')
      if shows != None:
        shows = shows.findAll('h3', 'showpass')
        for show in shows:
          name = Util.normalizeText(show.nextSibling.strong.text)
          img = show.img['data-original']
          index = img.rfind('?')
          show.nextSibling.strong.extract()
          li = Util.createListItem(name, thumbnailImage = img[:index], streamtype = 'video', infolabels = { 'title' : name, 'plot' : Util.normalizeText(show.nextSibling.text) })
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 's', 'path' : show.a['href'] }), li, True)
        xbmcplugin.endOfDirectory(self._handle)

    # Stagioni.
    elif self._params['action'] == 's':
      response = self._getMTVResponse(self._params['path'])
      if response != None:
        if response.renderContents().find('<h2>Troppo tardi! <b>&#9787;</b></h2>') == -1:
          seasons = response.find('ul', 'nav').findAll('a')
          if len(seasons) > 1:
            title = response.find('h1', { 'itemprop' : 'name' }).text
            for season in seasons:
              link = season['href']
              season = Util.normalizeText(season.text)
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
      videoId = Util.getHtml(self._params['path'], True)
      if videoId != None:
        videoId = videoId.find('div', 'MTVNPlayer')
        if videoId != None:
          videoId = videoId['data-contenturi']
          response = Util.getHtml('http://intl.esperanto.mtvi.com/www/xml/media/mediaGen.jhtml?uri=mgid:uma:video:mtv.it{0}'.format(videoId[videoId.rfind(':'):]), True)
          if response != None:
            response = response.findAll('rendition')
            streams = []
            for stream in response:
              streams.append([ int(stream['duration']), int(stream['bitrate']), stream.src.text ])
            streams.sort(key = itemgetter(1), reverse = True)
            idLabel = 30008 - len(streams)
            for duration, bitrate, url in streams:
              title = Util.getTranslation(idLabel)
              idLabel += 1
              li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title }, duration = duration)
              xbmcplugin.addDirectoryItem(self._handle, '{0} swfUrl=http://media.mtvnservices.com/player/prime/mediaplayerprime.2.3.7.swf?uri={1}.swf swfVfy=true'.format(url, self._params['path']), li, False)
            xbmcplugin.endOfDirectory(self._handle)
        else:
          xbmcgui.Dialog().ok(Util._addonName, Util.showVideoNotAvailableDialog()) # Video non disponibile.


  def _getMTVResponse(self, link):
    return Util.getHtml('http://ondemand.mtv.it{0}'.format(link), True)


  def _getEpisodes(self, path):
    index = path.rfind('/')
    videos = self._getMTVResponse('{0}.rss'.format(path[:index]))
    if videos != None:
      videos = videos.findAll('item')
      season = '{0}/'.format(path[index:])
      for video in videos:
        if video.link.nextSibling.find(season) > -1:
          name = Util.normalizeText(video.title.text)
          img = video.enclosure['url']
          iResEnd = img.rfind('.')
          iResStart = iResEnd - 3
          if img[iResStart:iResEnd] == '140':
            img = '{0}640{1}'.format(img[:iResStart], img[iResEnd:])
          li = Util.createListItem(name, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : name, 'plot' : Util.normalizeText(video.description.text) })
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 'r', 'path' : video.link.nextSibling }), li, True)
      xbmcplugin.endOfDirectory(self._handle)


# Entry point.
#startTime = datetime.datetime.now()
mtv = MTV()
del mtv
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
