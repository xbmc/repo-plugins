#!/usr/bin/python
import re, sys, xbmcplugin#, datetime
from neverwise import Util
from datetime import timedelta


class Dplay(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    # Shows.
    if len(self._params) == 0:
      shows = Util.getResponseJson('http://it.dplay.com/api/v2/ajax/modules?items=1000&page_id=32&module_id=26')
      if shows.isSucceeded:
        for show in shows.body['data']:
          episodes = 0
          for ti in show['taxonomy_items']:
            if ti['type'] == 'show':
              episodes = ti['metadata']['episodes']
              break # Stops "for ti in show['taxonomy_items']:".
          title = Util.getTranslation(30009).format(show = show['title'], number = episodes)
          img = show['image_data']
          li = Util.createListItem(title, thumbnailImage = self._getImage(img), streamtype = 'video', infolabels = { 'title' : title, 'plot' : show['description'] })
          xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 's', 'showid' : show['id'] }), li, True)
        xbmcplugin.endOfDirectory(self._handle)

    # Seasons.
    elif self._params['action'] == 's':
      headers = { 'User-Agent' : 'Dalvik/2.1.0 (Linux; U; Android 5.1.1; D6503 Build/23.4.A.0.546)' }
      url = 'http://it.dplay.com/api/v1/content/device/shows/{0}/seasons?realm=DPLAYIT&appVersion=2.0.0&platform=ANDROID&platformVersion=5.1.1'.format(self._params['showid'])
      seasons = Util.getResponseJson(url, headers)
      if seasons.isSucceeded:
        if xbmcplugin.getSetting(self._handle, 'show_seasons') == 'false' or len(seasons.body['data']) > 1:
          for season in seasons.body['data']:
            title = Util.getTranslation(30010).format(season = season['name'], numberof = season['episodes_available'], numbertot = season['episodes_total'])
            li = Util.createListItem(title, thumbnailImage = 'DefaultFolder.png', streamtype = 'video', infolabels = { 'title' : title })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 'e', 'showid' : self._params['showid'], 'seasonid' : season['id'] }), li, True)
          xbmcplugin.endOfDirectory(self._handle)
        else:
          self._getEpisodes(self._params['showid'], seasons.body['data'][0]['id'])

    # Episodes.
    elif self._params['action'] == 'e':
      self._getEpisodes(self._params['showid'], self._params['seasonid'])

    # Play video.
    elif self._params['action'] == 'v':
      stream = Util.getResponseForRegEx(self._params['url'])
      if stream.isSucceeded:
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
        urls = re.findall('RESOLUTION=.+?x(.+?),CODECS=".+?"(.+?)#', stream.body)
        items = []
        for qly, url in urls:
          items.append(( abs(qlySetting - int(qly)), url ))
        items = sorted(items, key = lambda item: item[0])
        Util.playStream(self._handle, '', path = items[0][1])


  def _getEpisodes(self, showId, seasonId):
    url = 'http://it.dplay.com/api/v2/ajax/shows/{0}/seasons/{1}?show_id={0}&items=50&sort=episode_number_asc&video_types=-clip&season_id={1}'.format(showId, seasonId)
    episodes = Util.getResponseJson(url)
    if episodes.isSucceeded:
      for episode in episodes.body['data']:
        if episode['title'].lower().find('episodio') > -1:
          title = episode['title']
        else:
          title = Util.getTranslation(30011).format(episode = episode['title'], number = episode['episode'])
        img = episode['image_data']
        desc = episode['description'] or episode['video_metadata_longDescription']
        time = self._getDuration(int(episode['video_metadata_length']))
        li = Util.createListItem(title, thumbnailImage = self._getImage(img), streamtype = 'video', infolabels = { 'title' : title, 'plot' : desc }, duration = time, isPlayable = True)
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'action' : 'v', 'url' : episode['hls'] }), li)
      xbmcplugin.endOfDirectory(self._handle)


  def _getImage(self, image):
    if image is not None:
      return u'{0}c_fill,h_246,w_368/{1}'.format('http://res.cloudinary.com/db79cecgq/image/upload/', image['file'])
    else:
      return 'DefaultVideo.png'


  def _getDuration(self, milliseconds):
    return str(timedelta(milliseconds/1000.0))


# Entry point.
#startTime = datetime.datetime.now()
dplay = Dplay()
del dplay
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
