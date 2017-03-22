#!/usr/bin/python
import neverwise as nw, os, re, sys, xbmcplugin#, datetime
from datetime import timedelta


class Dplay(object):

  _handle = int(sys.argv[1])
  _params = nw.urlParametersToDict(sys.argv[2])
  _channels = []

  def __init__(self):

    # Data.
    self._channels.append({ 'id' : 13, 'text' : 'DMAX', 'logo' : 'v1435134631/DMAX_logo_makrqn.jpg', 'fanart' : 'v1476968287/DMAX_channel_3_quxfpy.jpg' })
    self._channels.append({ 'id' : 11964, 'text' : 'Focus', 'logo' : 'v1430902724/Focus_channel_logo_x5ffc6.png', 'fanart' : 'v1430902770/Focus_channel_3_image_qcotbl.jpg' })
    self._channels.append({ 'id' : 18010, 'text' : 'Frisbee', 'logo' : 'v1447775998/FRISBEE_LOGO_Mktg_tepxuy.png', 'fanart' : 'v1475572068/Frisbee_channel_image_tsxtgk.jpg' })
    self._channels.append({ 'id' : 8882, 'text' : 'Giallo', 'logo' : 'v1430903282/Logo_Giallo_png_360_qok7dz.png', 'fanart' : 'v1442327197/Dplay_Giallo_imgchannelpage_1600_bsvcqo.jpg' })
    self._channels.append({ 'id' : 16414, 'text' : 'K2', 'logo' : 'v1444060838/K2_channel_logo_oz9qxo.png', 'fanart' : 'v1444222560/K2_channel_2_image_u7wa6t.jpg' })
    self._channels.append({ 'id' : 20186, 'text' : 'NOVE', 'logo' : 'v1475055469/NOVE_Channel_Logo_WHite_NEW_jc5tgy.png', 'fanart' : 'v1475481860/Deejay_channel_2000_4_mbjrnd.jpg' })
    self._channels.append({ 'id' : 14, 'text' : 'Real Time', 'logo' : 'v1426782642/Realtime_Channel_Logo_bmawaq.png', 'fanart' : 'v1472842523/Real_Time_img_canale_nuovo_3_best_fvhoww.jpg' })
    self._channels.append({ 'id' : 21663, 'text' : 'Dplay original', 'logo' : 'v1456912515/Dplay_Original_bug_king2w.png', 'fanart' : 'v1456912849/Dplay_Original_poster_frame_qtr878.jpg' })

    show_channels = xbmcplugin.getSetting(self._handle, 'show_channels')

    # Main menu.
    if len(self._params) == 0 and show_channels == 'true':
      fanart = os.path.join(nw.addon.getAddonInfo('path'), 'fanart.jpg')
      self._addItem(nw.getTranslation(30013), { 'action' : 'p', 'page' : 0 }, fanart = fanart)
      self._addItem(nw.getTranslation(30014), { 'action' : 'c' }, fanart = fanart)
      xbmcplugin.endOfDirectory(self._handle)

    # Shows.
    elif show_channels == 'false' or self._params['action'] == 'p':
      page = self._params['page'] if 'page' in self._params else 0
      items = xbmcplugin.getSetting(self._handle, 'items_per_page')
      hide_show_no_ep = xbmcplugin.getSetting(self._handle, 'hide_show_no_ep')
      url = None
      channel = None
      if 'channel' in self._params:
        channel = self._params['channel']
        url = 'http://it.dplay.com/api/v2/ajax/shows/?items={0}&homechannel_id={2}&page={1}&sort='.format(items, '{0}', channel)
      else:
        url = 'http://it.dplay.com/api/v2/ajax/modules?items={0}&page_id=32&module_id=26&page={1}'.format(items, '{0}')
      self._getShowsPage(url, page, hide_show_no_ep, channel)

    # Channels.
    elif self._params['action'] == 'c':
      for channel in self._channels:
        self._addChannel(channel['text'], { 'action' : 'p', 'page' : 0, 'channel' : channel['id'] }, channel['logo'], channel['fanart'])
      xbmcplugin.endOfDirectory(self._handle)

    # Seasons.
    elif self._params['action'] == 's':
      url = 'http://it.dplay.com/api/v1/content/device/shows/{0}/seasons?realm=DPLAYIT&appVersion=2.0.0&platform=ANDROID&platformVersion=5.1.1'.format(self._params['showid'])
      seasons = nw.getResponseJson(url)
      if seasons.isSucceeded:
        if xbmcplugin.getSetting(self._handle, 'show_seasons') == 'false' or len(seasons.body['data']) > 1:
          for season in seasons.body['data']:
            title = nw.getTranslation(30016).format(season = season['name'], numberof = season['episodes_available'], numbertot = season['episodes_total'])
            self._addItem(title, { 'action' : 'e', 'showid' : self._params['showid'], 'seasonid' : season['id'] }, 'DefaultFolder.png', self._findFanart(self._params['channel']))
          xbmcplugin.endOfDirectory(self._handle)
        else:
          self._getEpisodes(self._params['showid'], seasons.body['data'][0]['id'])

    # Episodes.
    elif self._params['action'] == 'e':
      self._getEpisodes(self._params['showid'], self._params['seasonid'])

    # Play video.
    elif self._params['action'] == 'v':
      stream = nw.getResponseForRegEx(self._params['url'])
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
          items.append(( abs(qlySetting - int(qly)), url.strip() ))
        items = sorted(items, key = lambda item: item[0])
        nw.playStream(self._handle, '', path = items[0][1])


  def _getShowsPage(self, url, page, hide_show_no_ep, channel):
    shows = nw.getResponseJson(url.format(page))
    if shows.isSucceeded:
      for show in shows.body['data']:
        episodes = 0
        channel_id = 0
        for ti in show['taxonomy_items']:
          if ti['type'] == 'show':
            episodes = ti['metadata']['episodes']
          elif ti['type'] == 'home-channel':
            channel_id = ti['term_id']
        if hide_show_no_ep == 'false' or episodes != '0':
          title = nw.getTranslation(30015).format(show = show['title'], number = episodes)
          img = show['image_data']
          self._addItem(title, { 'action' : 's', 'showid' : show['id'], 'channel' : channel_id }, self._getUrlImgPreview(img), self._findFanart(channel_id), show['description'])
      pages = shows.body['total_pages']
      page = int(page)
      if page < pages - 1:
        if xbmcplugin.getSetting(self._handle, 'use_pagination') == 'true':
          if channel != None:
            nw.createNextPageItem(self._handle, page + 2, { 'action' : 'p', 'page' : page + 1, 'channel' : channel })
          else:
            nw.createNextPageItem(self._handle, page + 2, { 'action' : 'p', 'page' : page + 1 })
          xbmcplugin.endOfDirectory(self._handle)
        else:
          self._getShowsPage(url, page + 1, hide_show_no_ep, channel)
      else:
        xbmcplugin.endOfDirectory(self._handle)


  def _addChannel(self, title, keyValueUrlList, logo, fanart):
    logo = self._getUrlImg(logo, 'c_fill,w_368')
    fanart = self._getUrlImgFanart(fanart)
    self._addItem(title, keyValueUrlList, logo, fanart)


  def _addItem(self, title, keyValueUrlList, logo = 'DefaultFolder.png', fanart = None, plot = None, duration = '', isPlayable = False):
    li = nw.createListItem(title, thumbnailImage = logo, fanart = fanart, streamtype = 'video', infolabels = { 'title' : title, 'plot' : plot }, duration = duration, isPlayable = isPlayable)
    xbmcplugin.addDirectoryItem(self._handle, nw.formatUrl(keyValueUrlList), li, not isPlayable)


  def _getEpisodes(self, showId, seasonId):
    url = 'http://it.dplay.com/api/v2/ajax/shows/{0}/seasons/{1}?show_id={0}&items=50&sort=episode_number_asc&video_types=-clip&season_id={1}'.format(showId, seasonId)
    episodes = nw.getResponseJson(url)
    if episodes.isSucceeded:
      for episode in episodes.body['data']:
        if episode['title'].lower().find('episodio') > -1:
          title = episode['title']
        else:
          title = nw.getTranslation(30017).format(episode = episode['title'], number = episode['episode'])
        fanart = None
        for ti in episode['taxonomy_items']:
          if ti['type'] == 'home-channel':
            fanart = self._findFanart(ti['term_id'])
            break # Stops "for ti in show['taxonomy_items']:".
        img = episode['image_data']
        desc = episode['description'] or episode['video_metadata_longDescription']
        time = self._getDuration(int(episode['video_metadata_length']))
        self._addItem(title, { 'action' : 'v', 'url' : episode['hls'] }, self._getUrlImgPreview(img), fanart, desc, time, True)
      xbmcplugin.endOfDirectory(self._handle)


  def _getUrlImg(self, image, paramsImg):
    return u'http://res.cloudinary.com/db79cecgq/image/upload/{0}/{1}'.format(paramsImg, image)


  def _getUrlImgPreview(self, image):
    if image is not None:
      return self._getUrlImg(image['file'], 'c_fill,h_246,w_368')
    else:
      return 'DefaultVideo.png'


  def _getUrlImgFanart(self, image):
    #return self._getUrlImg(image, 'c_fill,h_720,w_1280')
    return self._getUrlImg(image, '')


  def _findFanart(self, channel_id):
    for channel in self._channels:
      if channel['id'] == int(channel_id):
        return self._getUrlImgFanart(channel['fanart']) # Stops "for channel in self._channels:" and return url.


  def _getDuration(self, milliseconds):
    return str(timedelta(milliseconds/1000.0))


# Entry point.
#startTime = datetime.datetime.now()
dplay = Dplay()
del dplay
#xbmc.log('{0} azione {1}'.format(nw.addonName, str(datetime.datetime.now() - startTime)))
