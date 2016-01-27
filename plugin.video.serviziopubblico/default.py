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
      response = Util.getResponseBS(self._createPage(self._params['page']))
      if response.isSucceeded:

        # Archivi (santoro, vauro, travaglio, dragoni, puntate, argomenti e inviati).
        if self._params['id'] == 'i':
          self._showArchiveList(response.body, self._params['id'])

        # Argomenti.
        elif self._params['id'] == 't':
          categs = response.body.findAll('div', 'col-xs-12 single-argomento')
          for categ in categs:
            title = categ.a['title']
            img = 'DefaultVideo.png'
            if categ.img != None:
              img = self._normalizeImage(categ.img['src'])
            li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title, 'plot' : categ.div.renderContents() })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'r', 'page' : categ.a['href'] }), li, True)
          self._showNextPage(response.body, self._params['id'])
          xbmcplugin.endOfDirectory(self._handle)

        # Gli inviati.
        elif self._params['id'] == 'n':
          envoys = response.body.findAll('div', { 'class' : re.compile('post-[0-9]+ persone.+?') })
          for envoy in envoys:
            title = envoy.a['title']
            li = Util.createListItem(title, thumbnailImage = self._normalizeImage(envoy.img['src']), streamtype = 'video', infolabels = { 'title' : title })
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'i', 'page' : envoy.a['href'] }), li, True)
          xbmcplugin.endOfDirectory(self._handle)

        # Ricerca categID.
        elif self._params['id'] == 'r':
          categid = re.search('\?cat_id=([0-9]+)"', response.body.renderContents())
          if categid != None:
            categid = categid.group(1)
            link = self._GetSPPage('/?p=15546&cat_id={0}'.format(categid))
            if categid == '2': # Per evitare di mangiarsi un video adotto questo barbatrucco.
              link = self._GetSPPage('/?p=15526&cat_id=2')
            response = Util.getResponseBS(link)
            if response.isSucceeded:
              self._showArchiveList(response.body, 'i')

        # Riproduzione del video.
        elif self._params['id'] == 'v':
          img = response.body.find('meta', { 'property' : 'og:image' })['content']
          tide = response.body.find('h3', 'entry-title')

          responseString = response.body.renderContents()

          # Servizio pubblico.
          if responseString.find('meride-video-container') > -1:
            self._playVideo(response.body, tide.text, img, tide.parent.text)

          # Fatto quotidiano.
          elif responseString.find('<object id="flashObj"') > -1:
            urlParam = response.body.find('param', { 'name' : 'flashVars' })['value']
            urlParam = re.search("linkBaseURL=(.+?)&", urlParam).group(1).replace('%3A', ':').replace('%2F', '/')
            url = Util.formatUrl({ 'id' : 'v', 'page' : urlParam }, 'plugin://plugin.video.fattoquotidianotv/')
            Util.playStream(self._handle, tide.text, img, url, 'video', { 'title' : tide.text, 'plot' : tide.parent.text })

          else:
            Util.showVideoNotAvailableDialog()

        # Riproduzione video esterna.
        elif self._params['id'] == 'e':
          self._playVideo(response.body, self._params['title'], self._params['img'], self._params['descr'])


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
        Util.createNextPageItem(self._handle, nextPage.text, { 'id' : urlId, 'page' : nextPage['href'] })


  def _showList(self, html, urlId):
    videos = html.findAll('div', { 'class' : re.compile('post-[0-9]+ (?:post|puntate).+?') })
    for video in videos:
      if video.find('div', 'icon-post flaticon-facetime') != None:
        title = video.a['title']
        descr = video.find('div', 'post-content')
        descr.a.extract()
        img = 'DefaultVideo.png'
        if video.img != None:
          img = self._normalizeImage(video.img['src'])
        li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title, 'plot' : descr.text }, isPlayable = True)
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
      response = Util.getResponseBS('http://mediasp.meride.tv/embedproxy.php/{0}/folder1/{1}/desktop'.format(urlParam['data-customer'], urlParam['data-embed']))
      if response.isSucceeded:
        try:
          Util.playStream(self._handle, title, img, response.body.iphone.text, 'video', { 'title' : title, 'plot' : descr })
        except:
          Util.playStream(self._handle, title, img, response.body.mp4.text, 'video', { 'title' : title, 'plot' : descr })


# Entry point.
#startTime = datetime.datetime.now()
sp = ServizioPubblico()
del sp
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
