#!/usr/bin/python
import re, sys, xbmcplugin#, datetime
from neverwise import Util


class ServizioPubblico(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    # Visualizzazione del menu.
    if len(self._params) == 0:
      categs = []
      categs.append(['Santoro', 'r', '/canali/santoro'])
      categs.append(['Vauro', 'r', '/canali/vauro'])
      categs.append(['Travaglio', 'r', '/canali/travaglio'])
      categs.append(['Dragoni', 'r', '/canali/dragoni'])
      categs.append(['Puntate', 'i', '/puntate'])
      categs.append(['Argomenti', 't', '/argomenti'])
      categs.append(['Gli inviati', 'n', '/gli-inviati'])
      for title, paramId, page in categs:
        li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title })
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : paramId, 'page' : page }), li, True)
      xbmcplugin.endOfDirectory(self._handle)
    else:
      response = Util.getHtml(self._createPage(self._params['page']), True)
      if response != None:

        # Archivi (santoro, vauro, travaglio, dragoni, puntate, argomenti e inviati).
        if self._params['id'] == 'i':
          self._showArchiveList(response, self._params['id'])

        # Argomenti.
        elif self._params['id'] == 't':
          categs = response.findAll('div', 'col-xs-12 single-argomento')
          for categ in categs:
            title = Util.normalizeText(categ.a['title'])
            li = Util.createListItem(title, thumbnailImage = self._normalizeImage(categ.img['src']), streamtype = 'video', infolabels = { 'title' : title, 'plot' : Util.normalizeText(Util.trimTags(categ.div.renderContents())) })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'r', 'page' : categ.a['href'] }), li, True)
          self._showNextPage(response, self._params['id'])
          xbmcplugin.endOfDirectory(self._handle)

        # Gli inviati.
        elif self._params['id'] == 'n':
          envoys = response.findAll('div', { 'class' : re.compile('post-[0-9]+ persone.+?') })
          for envoy in envoys:
            title = Util.normalizeText(envoy.a['title'])
            li = Util.createListItem(title, thumbnailImage = self._normalizeImage(envoy.img['src']), streamtype = 'video', infolabels = { 'title' : title })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'i', 'page' : envoy.a['href'] }), li, True)
          xbmcplugin.endOfDirectory(self._handle)

        # Ricerca categID.
        elif self._params['id'] == 'r':
          categid = re.compile('\?cat_id=([0-9]+)"').findall(response.renderContents())
          if len(categid) > 0:
            categid = categid[0]
            link = self._GetSPPage('/?p=15546&cat_id={0}'.format(categid))
            if categid == '2': # Per evitare di mangiarsi un video adotto questo barbatrucco.
              link = self._GetSPPage('/?p=15526&cat_id=2')
            response = Util.getHtml(link, True)
            if response != None:
              self._showArchiveList(response, 'i')

        # Riproduzione del video.
        elif self._params['id'] == 'v':
          img = response.find('meta', { 'property' : 'og:image' })['content']
          tide = response.find('h3', 'entry-title')
          title = Util.normalizeText(tide.text)
          descr = Util.normalizeText(Util.trimTags(tide.parent.text))

          responseString = response.renderContents()

          # Servizio pubblico.
          if responseString.find('meride-video-container') > -1:
            self._playVideo(response, title, img, descr)

          # Fatto quotidiano.
          elif responseString.find('<object id="flashObj"') > -1:
            urlParam = response.find('param', { 'name' : 'flashVars' })['value']
            urlParam = re.search("linkBaseURL=(.+?)&", urlParam).group(1).replace('%3A', ':').replace('%2F', '/')
            url = Util.formatUrl({ 'id' : 'v', 'page' : urlParam }, 'plugin://plugin.video.fattoquotidianotv/')
            Util.playStream(self._handle, title, img, url, 'video', { 'title' : title, 'plot' : descr })

          else:
            Util.showVideoNotAvailableDialog()

        # Riproduzione video esterna.
        elif self._params['id'] == 'e':
          self._playVideo(response, self._params['title'], self._params['img'], self._params['descr'])


  def _GetSPPage(self, link):
    return 'http://www.serviziopubblico.it{0}'.format(link)


  def _createPage(self, link):
    if not link.startswith('http://') and not link.startswith('https://'):
      if link[0:1] == '/':
        return self._GetSPPage(link)
      else:
        return self._GetSPPage('/{0}'.format(link))
    else:
      return link


  def _normalizeImage(self, image):
    subImg = image[image.rfind('-'):image.rfind('.')]
    result = self._createPage(image.replace(subImg, ''))
    if re.match('[0-9]+x[0-9]+', subImg) == None:
      result = self._createPage(image)
    return result


  def _showNextPage(self, html, urlId):
    nextPage = html.find('span', 'current')
    if nextPage != None:
      nextPage = nextPage.nextSibling
      if nextPage != None and len(str(nextPage)) < 2:
        nextPage = nextPage.nextSibling
      if nextPage != None:
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : urlId, 'page' : Util.normalizeText(nextPage['href']) }), Util.createItemPage(Util.normalizeText(nextPage.text)), True)


  def _showList(self, html, urlId):
    videos = html.findAll('div', { 'class' : re.compile('post-[0-9]+ (?:post|puntate).+?') })
    for video in videos:
      if video.find('div', 'icon-post flaticon-facetime') != None:
        title = Util.normalizeText(video.a['title'])
        descr = video.find('div', 'post-content')
        descr.a.extract()
        li = Util.createListItem(title, thumbnailImage = self._normalizeImage(video.img['src']), streamtype = 'video', infolabels = { 'title' : title, 'plot' : Util.normalizeText(descr.text) }, isPlayable = True)
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : video.a['href'] }), li, False)
    self._showNextPage(html, urlId)
    xbmcplugin.endOfDirectory(self._handle)


  def _showArchiveList(self, html, urlId):
    html = html.find('div', 'col-xs-8 right-border')
    seeMore = html.find('div', 'see-more-container')
    if seeMore != None:
      seeMore.extract()
    self._showList(html, urlId)


  def _playVideo(self, response, title, img, descr):
    urlParam = response.find('div', 'meride-video-container')
    if urlParam != None:
      response = Util.getHtml('http://mediasp.meride.tv/embedproxy.php/{0}/folder1/{1}/desktop'.format(urlParam['data-customer'], urlParam['data-embed']), True)
      if response != None:
        try:
          Util.playStream(self._handle, title, img, response.iphone.text, 'video', { 'title' : title, 'plot' : descr })
        except:
          Util.playStream(self._handle, title, img, response.mp4.text, 'video', { 'title' : title, 'plot' : descr })


# Entry point.
#startTime = datetime.datetime.now()
sp = ServizioPubblico()
del sp
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
