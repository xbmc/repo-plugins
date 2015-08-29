#!/usr/bin/python
import re, sys, os, xbmcplugin, xbmcgui#, datetime
from neverwise import Util


class VirginRadio(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])
  _webradioRe = re.compile('webradio', re.IGNORECASE)

  def __init__(self):

    # Visualizzo i video della sezione.
    if self._params.get('content_type') is None:
      response = self._getVirginResponse(self._params['page'], True)
      if response != None:

        # Riproduzione di un video.
        if self._params['id'] == 'v':
          title = Util.normalizeText(response.find('meta', { 'property' : 'og:title' })['content'])
          img = response.find('meta', { 'property' : 'og:image' })['content']
          descr = Util.normalizeText(response.find('meta', { 'property' : 'og:description' })['content'])
          textHtml = response.renderContents()
          server = re.compile('netConnectionUrl: "rtmp://(.+?)/(.+?)/').findall(textHtml)
          play = response.find('a', 'player plain')['href']
          play = re.compile('(.+?):(.+)').findall(play)
          Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={3}:{2} pageURL=http://www.virginradio.it swfVfy=true live=false flashVer=LNX 10,1,82,76'.format(server[0][0], server[0][1], play[0][1], play[0][0]), 'video', { 'title' : title, 'plot' : descr })

        # Riproduzione di una radio.
        elif self._params['id'] == 'r':
          streamParam = self._getStreamParam(1)
          if streamParam != None:
            title = Util.normalizeText(self._webradioRe.sub('', response.find('meta', { 'property' : 'og:title' })['content']).strip())
            img = self._makeImageUrl(response.find('img', 'lazy')['data-original'])
            descr = Util.normalizeText(response.find('div', 'testo taglia_testo').text)
            params = re.compile('streamRadio=(.+?)&radioName=(.+?)&').findall(response.find('param', {'name' : 'movie'})['value'])
            Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://www.virginradio.it/wp-content/themes/wirgin/corePlayerStreamingVisible2013_counter_VIRGIN.swf?streamRadio={2}&radioName={3}&autoPlay=1&bufferTime=2.5&rateServer=37.247.51.47 pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], params[0][0], params[0][1].replace(' ', '%20')), 'music', { 'title' : title, 'plot' : descr })

    # Diretta e video.
    elif self._params['content_type'] == 'video':
      qlty = int(xbmcplugin.getSetting(self._handle, 'vid_quality')) + 1
      streamParam = self._getStreamParam(qlty)
      if streamParam != None:
        response = self._getVirginResponse('/video')
        if response != None:
          title = Util.getTranslation(30003)
          img = '{0}/resources/images/VirginRadioTV.png'.format(os.path.dirname(os.path.abspath(__file__)))
          li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title }) # Diretta.
          url = 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://video.virginradioitaly.it/com/universalmind/swf/video_player_102.swf?xmlPath=http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml&advXML=http://video.virginradioitaly.it/com/universalmind/adsWizzConfig/1.xml pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], streamParam[2])
          xbmcplugin.addDirectoryItem(self._handle, url, li, False)
          videos = response.findAll('div', 'anteprima_articolo article_cont')
          for video in videos:
            title = Util.normalizeText(video.a.img['title'])
            img = self._makeUrl(video.a.img['data-original']).replace('206/122', '600/315')
            descr = ''
            if video.h3 != None:
              descr = Util.normalizeText(video.h3.a.text)
            li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title, 'plot' : descr }, isPlayable = True)
            url = Util.formatUrl({ 'id' : 'v', 'page' : video.a['href'].replace('http://www.virginradio.it', '') })
            xbmcplugin.addDirectoryItem(self._handle, url, li, False)

      if (streamParam == None or not streamParam) and (response == None or not response): # Se sono vuoti oppure liste vuote.
        xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30004)) # Errore recupero stream diretta.

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    # Web radio.
    elif self._params['content_type'] == 'audio':
      response = self._getVirginResponse('/webradio', True)
      if response != None:
        divs = response.findAll('div', { 'class' : re.compile('.+') })
        for div in divs:
          if div['class'].find('overbox_vrg_article_preview_webradio') > -1:
            radios = div.findAll('div', 'anteprima_articolo article_cont')
            for radio in radios:
              title = Util.normalizeText(self._webradioRe.sub('', radio.a.img['title']).strip())
              img = self._makeImageUrl(radio.a.img['data-original'])
              li = Util.createListItem(title, thumbnailImage = img, streamtype = 'music', infolabels = { 'title' : title }, isPlayable = True)
              url = Util.formatUrl({ 'id' : 'r', 'page' : radio.a['href'].replace('http://www.virginradio.it', '') })
              xbmcplugin.addDirectoryItem(self._handle, url, li, False)
          elif div['class'].find('text_edit') > -1 and div['class'].find('vrg_box_title_webradio') > -1 and div['class'].find('last') > -1:
            break # Stops "for div in divs:".
        xbmcplugin.endOfDirectory(self._handle)


  def _makeUrl(self, link):
    domain = 'http://www.virginradio.it'
    if link[0] == '/':
      return '{0}{1}'.format(domain, link)
    else:
      return '{0}/{1}'.format(domain, link)


  def _getVirginResponse(self, link, showErrorDialog = False):
    return Util.getHtml(self._makeUrl(link), showErrorDialog)


  def _getStreamParam(self, quality):
    result = None
    response = Util.getHtml('http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml')
    if response != None:
      serverParam = re.compile('auto\|(.+?)\|(.+)').findall(response.find('serverpath')['value'])
      result = [serverParam[0][0], serverParam[0][1], response.find('rate', {'n' : str(quality)})['streamname']]
    return result


  def _makeImageUrl(self, imgUrl):
    path = re.compile('resizer/[0-9]+/[0-9]+/true')
    img = path.sub('upload', self._makeUrl(imgUrl))

    index = img.find('--')
    if index > -1:
      img = img [:index]

    return img


# Entry point.
#startTime = datetime.datetime.now()
vr = VirginRadio()
del vr
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
