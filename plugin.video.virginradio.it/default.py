#!/usr/bin/python
import re, sys, os, xbmcplugin, xbmcgui#, datetime
from neverwise import Util


class VirginRadio(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])
  _webradioRe = re.compile('webradio', re.IGNORECASE)

  def __init__(self):

    if len(self._params) == 0: # Scelta tra Audio o Video

      Util.createAudioVideoItems(self._handle)

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    elif len(self._params) == 1 and self._params['content_type'] == 'video': # Visualizzazione del menu video (diretta e video).
      qlty = int(xbmcplugin.getSetting(self._handle, 'vid_quality')) + 1
      streamParam = self._getStreamParam(qlty)
      if streamParam != None:
        response = self._getVirginResponse('/video')
        if response.isSucceeded:
          title = Util.getTranslation(30003)
          img = '{0}/resources/images/VirginRadioTV.png'.format(os.path.dirname(os.path.abspath(__file__)))
          li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title }) # Diretta.
          url = 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://video.virginradioitaly.it/com/universalmind/swf/video_player_102.swf?xmlPath=http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml&advXML=http://video.virginradioitaly.it/com/universalmind/adsWizzConfig/1.xml pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], streamParam[2])
          xbmcplugin.addDirectoryItem(self._handle, url, li, False)
          videos = response.body.findAll('div', 'anteprima_articolo article_cont')
          for video in videos:
            title = video.a.img['title']
            img = self._makeUrl(video.a.img['data-original']).replace('206/122', '600/315')
            descr = ''
            if video.h3 != None:
              descr = video.h3.a.text
            li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title, 'plot' : descr }, isPlayable = True)
            url = Util.formatUrl({ 'id' : 'v', 'page' : video.a['href'].replace('http://www.virginradio.it', '') })
            xbmcplugin.addDirectoryItem(self._handle, url, li, False)

      if (streamParam == None or not streamParam) and (response == None or not response): # Se sono vuoti oppure liste vuote.
        xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30004)) # Errore recupero stream diretta.

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    elif len(self._params) == 1 and self._params['content_type'] == 'audio': # Visualizzazione delle web radio.
      response = self._getVirginResponse('/webradio')
      if response.isSucceeded:
        divs = response.body.findAll('div', { 'class' : re.compile('.+') })
        for div in divs:
          if div['class'].find('overbox_vrg_article_preview_webradio') > -1:
            radios = div.findAll('div', 'anteprima_articolo article_cont')
            for radio in radios:
              title = self._webradioRe.sub('', radio.a.img['title']).strip()
              img = self._makeImageUrl(radio.a.img['data-original'])
              li = Util.createListItem(title, thumbnailImage = img, streamtype = 'music', infolabels = { 'title' : title }, isPlayable = True)
              url = Util.formatUrl({ 'id' : 'r', 'page' : radio.a['href'].replace('http://www.virginradio.it', '') })
              xbmcplugin.addDirectoryItem(self._handle, url, li, False)
          elif div['class'].find('text_edit') > -1 and div['class'].find('vrg_box_title_webradio') > -1 and div['class'].find('last') > -1:
            break # Stops "for div in divs:".
        xbmcplugin.endOfDirectory(self._handle)

    else:
      response = self._getVirginResponse(self._params['page'])
      if response.isSucceeded:

        # Riproduzione di un video.
        if self._params['id'] == 'v':
          title = response.body.find('meta', { 'property' : 'og:title' })['content']
          img = response.body.find('meta', { 'property' : 'og:image' })['content']
          descr = response.body.find('meta', { 'property' : 'og:description' })['content']
          textHtml = response.body.renderContents()
          server = re.search('netConnectionUrl: "rtmp://(.+?)/(.+?)/', textHtml)
          play = response.body.find('a', 'player plain')['href']
          play = re.search('(.+?):(.+)', play)
          Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={3}:{2} pageURL=http://www.virginradio.it swfVfy=true live=false flashVer=LNX 10,1,82,76'.format(server.group(1), server.group(2), play.group(2), play.group(1)), 'video', { 'title' : title, 'plot' : descr })

        # Riproduzione di una radio.
        elif self._params['id'] == 'r':
          streamParam = self._getStreamParam(1)
          if streamParam != None:
            title = self._webradioRe.sub('', response.body.find('meta', { 'property' : 'og:title' })['content']).strip()
            img = self._makeImageUrl(response.body.find('img', 'lazy')['data-original'])
            stream = re.search("onairXML = '(.+?)'", response.body.renderContents())
            if stream != None:
              Util.playStream(self._handle, title, img, stream.group(1), 'music', { 'title' : title })
            else:
              params = re.search('streamRadio=(.+?)&radioName=(.+?)&', response.body.find('param', {'name' : 'movie'})['value'])
              Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://www.virginradio.it/custom_widget/swf/corePlayerStreamingVisible2014_Virgin.swf?streamRadio={2}&radioName={3}&autoPlay=1&bufferTime=2.5&rateServer=37.247.51.47 pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], params.group(1), params.group(2).replace(' ', '%20')), 'music', { 'title' : title })

  def _makeUrl(self, link):
    domain = 'http://www.virginradio.it'
    if link.find(domain) == -1:
      if link[0] == '/':
        return '{0}{1}'.format(domain, link)
      else:
        return '{0}/{1}'.format(domain, link)
    else:
      return link


  def _getVirginResponse(self, link):
    return Util.getResponseBS(self._makeUrl(link))


  def _getStreamParam(self, quality):
    result = None
    response = Util.getResponseBS('http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml')
    if response.isSucceeded:
      serverParam = re.search('auto\|(.+?)\|(.+)', response.body.find('serverpath')['value'])
      result = [serverParam.group(1), serverParam.group(2), response.body.find('rate', {'n' : str(quality)})['streamname']]
    return result


  def _makeImageUrl(self, imgUrl):
    img = re.sub('resizer/[0-9]+/[0-9]+/true', 'upload', self._makeUrl(imgUrl))

    index = img.find('--')
    if index > -1:
      img = img [:index]

    return img


# Entry point.
#startTime = datetime.datetime.now()
vr = VirginRadio()
del vr
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
