#!/usr/bin/python
import re, sys, os, xbmcplugin, xbmcgui#, datetime
from neverwise import Util


class VirginRadio(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    # Visualizzo i video della sezione.
    if self._params.get('content_type') is None:
      response = self._getVirginResponse(self._params['page'], True)
      if response != None:

        # Video di una categoria.
        if self._params['id'] == 's':
          videos = response.findAll('article', 'casgin')
          for video in videos:
            title = Util.normalizeText(video.h3.text)
            imgs = video.findAll('img')
            img = imgs[0]['src']
            if img == '/wp-content/themes/wirgin/images/video-new.png':
              title += ' (NEW)'
              img = imgs[1]['src']
            li = Util.createListItem(title, thumbnailImage = self._normalizeImageUrl(img), streamtype = 'video', infolabels = { 'title' : title, 'plot' : Util.normalizeText(video.div.text) }, isPlayable = True)
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : video.a['href'] }), li, False)
          self._showNextPageDir(response.renderContents(), '[0-9]+ <a rel="nofollow" href="(.+?)">(.+?)</a>', 's')
          xbmcplugin.endOfDirectory(self._handle)

        # Riproduzione di un video.
        elif self._params['id'] == 'v':
          if response.find('title').text != 'Virgin Radio Tv': # Per evitare i video non funzionanti.
            title = Util.normalizeText(response.find('meta', { 'property' : 'og:title' })['content'])
            img = self._normalizeImageUrl(response.find('meta', { 'property' : 'og:image' })['content'])
            descr = response.find('meta', { 'property' : 'og:description' })['content']
            response = response.renderContents()
            play = re.compile('clip: \{"url":"(.+?):(.+?)"').findall(response)
            server = re.compile('"hddn":\{"url":"(.+?)","netConnectionUrl":"rtmp:\\\/\\\/(.+?)\\\/(.+?)"\},"').findall(response)
            playBS = play[0][1].replace('\\', '')
            Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={3}:{2} swfUrl={4} pageURL=http://www.virginradio.it swfVfy=true live=false flashVer=LNX 10,1,82,76'.format(server[0][1], server[0][2], playBS, play[0][0], server[0][0].replace('\\', '')), 'video', { 'title' : title, 'plot' : Util.normalizeText(descr) })
          else:
            Util.showVideoNotAvailableDialog()

        # Pagina successiva radio.
        elif self._params['id'] == 't':
          self._getWebRadio(response)

        # Riproduzione di una radio.
        elif self._params['id'] == 'r':
          streamParam = self._getStreamParam(1)
          if streamParam != None:
            title = Util.normalizeText(response.find('div', 'seo-strip clearfix').h1.text)
            img = response.find('meta', {'property' : 'og:image'})['content']
            #descr = response.find('meta', {'property' : 'og:description'})['content']
            params = re.compile('streamRadio=(.+?)&radioName=(.+?)&').findall(response.find('param', {'name' : 'movie'})['value'])
            Util.playStream(self._handle, title, img, 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://www.virginradio.it/wp-content/themes/wirgin/corePlayerStreamingVisible2013_counter_VIRGIN.swf?streamRadio={2}&radioName={3}&autoPlay=1&bufferTime=2.5&rateServer=37.247.51.47 pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], params[0][0], params[0][1].replace(' ', '%20')), 'music', { 'title' : title })

    # Diretta e categorie video.
    elif self._params['content_type'] == 'video':
      categs = []
      categs.append(['Virgin Radio TV', 'Guarda i migliori videoclip del canale Virgin Radio TV', '/video-canale/channel/1'])
      categs.append(['Garage Revolver', 'Guarda i migliori videoclip del canale Garage Revolver', '/video-canale/channel/2'])
      categs.append(['Video Community', 'Guarda i migliori videoclip del canale Video Community', '/video-canale/channel/4'])
      categs.append(['Musica', 'Guarda i migliori videoclip del canale Musica', '/video-canale/channel/5'])
      categs.append(['Wikipaola', 'Guarda i migliori videoclip del canale Wikipaola', '/video-canale/channel/7'])
      categs.append(['Heineken Jammin\' Festival', 'Guarda i migliori videoclip del canale Heineken Jammin\' Festival', '/video-canale/channel/9'])
      categs.append(['Virgin on Tour', 'Guarda i migliori videoclip del canale Virgin on Tour', '/video-canale/channel/12'])
      categs.append(['Virgin Radio VideoNews', 'Guarda i migliori videoclip del canale Virgin Radio VideoNews', '/video-canale/channel/13'])
      categs.append(['Virgin Rock 20', 'Guarda i migliori videoclip del canale Virgin Rock 20', '/video-canale/channel/14'])
      categs.append(['Giulia Sessions', 'Guarda i migliori videoclip del canale Giulia Sessions', '/video-canale/channel/15'])
      categs.append(['Elio Fiorucci\'s Stories', 'Guarda i migliori videoclip del canale Elio Fiorucci\'s Stories', '/video-canale/channel/17'])
      categs.append(['Virgin Rock Live', 'Guarda i migliori videoclip del canale Virgin Rock Live', '/video-canale/channel/18'])
      categs.append(['The Photograph', 'Guarda i migliori videoclip del canale The Photograph', '/video-canale/channel/19'])
      categs.append(['Litfiba Contest', 'Guarda i migliori videoclip del canale Litfiba Contest', '/video-canale/channel/20'])
      qlty = int(xbmcplugin.getSetting(self._handle, 'vid_quality')) + 1
      streamParam = self._getStreamParam(qlty)
      if streamParam != None:
        response = self._getVirginResponse('/video')
        if response != None:
          descr = Util.normalizeText(Util.trimTags(response.find('figcaption').parent.nextSibling.text))
          title = Util.normalizeText(response.find('span', 'h2Wrapper').text)
          img = '{0}/resources/images/VirginRadioTV.png'.format(os.path.dirname(os.path.abspath(__file__)))
          li = Util.createListItem(Util.getTranslation(30003), thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title, 'plot' : descr }) # Diretta.
          url = 'rtmp://{0}:1935/{1}/{2} app={1} playpath={2} swfUrl=http://video.virginradioitaly.it/com/universalmind/swf/video_player_102.swf?xmlPath=http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml&advXML=http://video.virginradioitaly.it/com/universalmind/adsWizzConfig/1.xml pageURL=http://www.virginradio.it swfVfy=true live=true timeout=30 flashVer=LNX 11,2,202,297'.format(streamParam[0], streamParam[1], streamParam[2])
          xbmcplugin.addDirectoryItem(self._handle, url, li, False)
      for nameCat, descr, link in categs:
        li = Util.createListItem(nameCat, streamtype = 'video', infolabels = { 'title' : nameCat, 'plot' : descr })
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 's', 'page' : link }), li, True)

      if (streamParam == None or not streamParam) and (response == None or not response): # Se sono vuoti oppure liste vuote.
        xbmcgui.Dialog().ok(Util._addonName, Util.getTranslation(30004)) # Errore recupero stream diretta.

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    # Web radio.
    elif self._params['content_type'] == 'audio':
      response = self._getVirginResponse('/webradio', True)
      if response != None:
        self._getWebRadio(response)


  def _getVirginResponse(self, link, showErrorDialog = False):
    return Util.getHtml('http://www.virginradio.it{0}'.format(link), showErrorDialog)


  def _getStreamParam(self, quality):
    result = None
    response = Util.getHtml('http://video.virginradioitaly.it/com/universalmind/tv/virgin/videoXML.xml')
    if response != None:
      serverParam = re.compile('auto\|(.+?)\|(.+)').findall(response.find('serverpath')['value'])
      result = [serverParam[0][0], serverParam[0][1], response.find('rate', {'n' : str(quality)})['streamname']]
    return result


  def _isExtensionNumber(self, extension):
    result = False
    try:
      int(extension)
      result = True
    except:
      pass
    return result


  def _normalizeImageUrl(self, img):
    extension = img[-3:]
    if extension[0] == '.':
      isNumber = self._isExtensionNumber(extension[-2:])
    else:
      isNumber = self._isExtensionNumber(extension)

    if isNumber:
      img = img.replace(extension, '.jpg')

    return img


  def _showNextPageDir(self, inputString, pattern, idParams):
    nextPage = re.compile(pattern).findall(inputString)
    if len(nextPage) > 0:
      xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : idParams, 'page' : nextPage[0][0] }), Util.createItemPage(Util.normalizeText(nextPage[0][1])), True)


  def _getWebRadio(self, response):
    radios = response.findAll('li', 'section-mood')
    #rList = re.compile('<img width="70" height="70" src="(.+?)".+?/> <a href="(.+?)">(.+?)</a> <p><p>(.+?)</p>').findall(response)
    for radio in radios:
      title = Util.normalizeText(radio.a.text)
      img = radio.img['src']
      subStr = img[img.rfind('-'):img.rfind('.')]
      li = Util.createListItem(title, thumbnailImage = img.replace(subStr, ''), streamtype = 'music', infolabels = { 'title' : title }, isPlayable = True)
      url = Util.formatUrl({ 'id' : 'r', 'page' : radio.a['href'].replace('http://www.virginradio.it', '') })
      xbmcplugin.addDirectoryItem(self._handle, url, li, False)
    self._showNextPageDir(response.renderContents(), '<span class="page-numbers current">.+?</span><a class="page-numbers" href="(.+?)">(.+?)</a>', 't')
    xbmcplugin.endOfDirectory(self._handle)


# Entry point.
#startTime = datetime.datetime.now()
vr = VirginRadio()
del vr
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
