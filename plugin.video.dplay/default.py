#!/usr/bin/python
import neverwise as nw, os, re, subprocess, sys, xbmcplugin
from datetime import timedelta#, datetime


class Dplay(object):

  _handle = int(sys.argv[1])
  _params = nw.urlParametersToDict(sys.argv[2])
  _access_token = None

  def __init__(self):
    fanart = nw.addon.getAddonInfo('fanart')

    if len(self._params) == 0:
      response = self._getResponseJson(None)
      if response.isSucceeded:
        #~ for menu in response.body['Menu']:
          #~ if menu['Url'] == None:
            #~ self._addItem(menu['Label'], { 'at' : self._access_token, 'action' : 'm', 'value' : re.sub('\s+', '', menu['Label']) }, fanart = fanart)
        #~ xbmcplugin.endOfDirectory(self._handle)
        response = self._getResponseJson('http://dplayproxy.azurewebsites.net//api/Show/GetList')
        for show in response.body:
          self._addItem(show['Name'], { 'at' : self._access_token, 'action' : 's', 'value' : show['Id'] }, show['Images'][0]['Src'], fanart, show['Description'])
        xbmcplugin.endOfDirectory(self._handle)
    else:
      self._access_token = self._params['at']

      if self._params['action'] == 's':
        response = self._getResponseJson('http://dplayproxy.azurewebsites.net/api/Show/GetById/?id={0}'.format(self._params['value']))
        if response.isSucceeded:
          if len(response.body['Sections']) > 0:
            fanart = response.body['Images'][0]['Src']
            time_zone = nw.gettzlocal()
            haveFFmpeg = os.path.isfile(nw.addon.getSetting('ffmpeg_path')) and os.path.isdir(nw.addon.getSetting('download_path'))
            for video in response.body['Sections'][0]['Items']:
              season_number = video['SeasonNumber']
              for video in video['Episodes']:
                vd = self._getVideoInfo(video, time_zone)
                cm = None
                params = { 'at' : self._access_token, 'action' : 'd', 'value' : video['Id'] }
                if haveFFmpeg:
                  cm = nw.getDownloadContextMenu('RunPlugin({0})'.format(nw.formatUrl(params)), vd['title'])
                params['action'] = 'v'
                self._addItem(vd['title'], params, vd['img'], fanart, vd['descr'], self._getDuration(video['Duration']), True, cm)
            xbmcplugin.endOfDirectory(self._handle)
          else:
            nw.showNotification(nw.getTranslation(30014))

      elif self._params['action'] == 'v':
        result = self._getStream(self._params['value'])
        if not result:
          nw.showVideoNotAvailable()
        else:
          nw.playStream(self._handle, result['title'], result['img'], result['url'], 'video', { 'title' : result['title'], 'plot' : result['descr'] })

      elif self._params['action'] == 'd':
        result = self._getStream(self._params['value'])
        if not result:
          nw.showVideoNotAvailable()
        else:
          name = ''.join([i if ord(i) < 128 else '' for i in result['title'].replace(' ', '_')])
          name = '{0}.ts'.format(name)
          os.chdir(nw.addon.getSetting('download_path'))
          #~ subprocess.call([nw.addon.getSetting('ffmpeg_path'), '-i', result['url'], '-c', 'copy', name])
          subprocess.Popen([nw.addon.getSetting('ffmpeg_path'), '-i', result['url'], '-c', 'copy', name])


  def _getStream(self, video_id):
    result = {}
    response = self._getResponseJson('http://dplayproxy.azurewebsites.net/api/Video/GetById/?id={0}'.format(video_id))
    if response.isSucceeded:
      vd = self._getVideoInfo(response.body)
      result['title'] = vd['title']
      result['descr'] = vd['descr']
      result['img'] = vd['img']
      response = self._getResponseJson('https://dplay-south-prod.disco-api.com/playback/videoPlaybackInfo/{0}'.format(video_id), True)
      if response.isSucceeded:
        url = response.body['data']['attributes']['streaming']['hls']['url']
        stream = nw.getResponse(url)
        if stream.isSucceeded:
          qlySetting = nw.addon.getSetting('vid_quality')
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
          else:
            qlySetting = 576
          strms_names = re.findall('RESOLUTION=.+?x(.+?),.+?".+?"\s(.+)', stream.body)
          items = []
          for qly, strm_name in strms_names:
            items.append(( abs(qlySetting - int(qly)), strm_name.strip() ))
          items = sorted(items, key = lambda item: item[0])
          i_end = url.find('?')
          i_start = url.rfind('/', 0, i_end) + 1
          old_str = url[i_start:i_end]
          result['url'] = url.replace(old_str, items[0][1])
    return result


  def _getResponseJson(self, url, add_bearer = False):

    token_url = 'http://dplayproxy.azurewebsites.net/api/config/init'
    if url == None or len(url) == 0:
      url = token_url

    response = nw.getResponseJson(url, self._getHeaders(add_bearer), False)
    if not response.isSucceeded:
      self._access_token = None
      response = nw.getResponseJson(token_url, self._getHeaders())
      if response.isSucceeded:
        self._access_token = response.body['Data']['AccessToken']
        response = nw.getResponseJson(url, self._getHeaders(add_bearer))

    if 'Data' in response.body:
      response.body = response.body['Data']

    if 'AccessToken' in response.body:
      self._access_token = response.body['AccessToken']

    return response


  def _getHeaders(self, add_bearer = False):

    default_headers = { 'User-Agent' : 'okhttp/3.3.0', 'Accept-Encoding' : 'gzip' }
    headers = None
    if self._access_token != None:
      headers = { 'AccessToken' : self._access_token }
      for key, value in default_headers.iteritems():
        headers[key] = value
    if headers == None:
      headers = default_headers
    if add_bearer:
      headers['Authorization'] = 'Bearer {0}'.format(self._access_token[0 : self._access_token.index('__!__') - len(self._access_token)])

    return headers


  def _getVideoInfo(self, video, time_zone = None):
    title = u'{0} ({1} {2} - {3} {4})'.format(video['Name'], nw.getTranslation(30011), video['SeasonNumber'], nw.getTranslation(30012), video['EpisodeNumber'])
    descr = video['Description']
    if video['PublishEndDate'] != None:
      if time_zone == None:
        time_zone = nw.gettzlocal()
      date = nw.strptime(video['PublishEndDate'], '%Y-%m-%dT%H:%M:%SZ')
      date = date.replace(tzinfo = nw.gettz('UTC'))
      date = date.astimezone(time_zone)
      descr = u'{0}\n\n{1} {2}'.format(descr, nw.getTranslation(30013), date.strftime(nw.datetime_format))
    return { 'img' : video['Images'][0]['Src'], 'title' : title, 'descr' : descr }


  def _addItem(self, title, keyValueUrlList, logo = 'DefaultFolder.png', fanart = None, plot = None, duration = '', isPlayable = False, contextMenu = None):
    li = nw.createListItem(title, thumbnailImage = logo, fanart = fanart, streamtype = 'video', infolabels = { 'title' : title, 'plot' : plot }, duration = duration, isPlayable = isPlayable, contextMenu = contextMenu)
    xbmcplugin.addDirectoryItem(self._handle, nw.formatUrl(keyValueUrlList), li, not isPlayable)


  def _getDuration(self, milliseconds):
    return str(timedelta(milliseconds/1000.0))


# Entry point.
#startTime = datetime.now()
dplay = Dplay()
del dplay
#xbmc.log('{0} azione {1}'.format(nw.addonName, str(datetime.now() - startTime)))
