#!/usr/bin/python
import re, sys, xbmcplugin, httplib#, datetime
from neverwise import Util
from pyamf import remoting


class FattoQTV(object):

  _handle = int(sys.argv[1])
  _params = Util.urlParametersToDict(sys.argv[2])

  def __init__(self):

    if len(self._params) == 0: # Visualizzazione del menu.

      # Menu.
      response = Util.getHtml('http://tv.ilfattoquotidiano.it', True)
      menuItems = []
      for ul in response.findAll('ul', 'nav-list'):
        for li in ul.findAll('li'):
          title = Util.normalizeText(li.a.text)
          link = li.a['href']
          li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title })
          menuItems.append(( li, link, title ))

      div = response.find('div', 'submenu-categories')
      for li in div.findAll('li'):
        link = li.a['href']
        found = False
        for item in menuItems:
          if item[1] == link:
            found = True
            break
        if not found:
          title = Util.normalizeText(li.a.text)
          li = Util.createListItem(title, streamtype = 'video', infolabels = { 'title' : title })
          menuItems.append(( li, link, title ))

      for item in sorted(menuItems, key = lambda item: item[2]):
        xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'c', 'page' : item[1] }), item[0], True)

      # Show items.
      xbmcplugin.endOfDirectory(self._handle)

    else:

      response = Util.getHtml(self._params['page'], True)
      if response != None:

        # Videos.
        if self._params['id'] == 'c': # Visualizzazione video di una categoria.
          videos = response.findAll('section', 'article-preview')
          for video in videos:
            divTitle = video.find('div', 'article-wrapper')
            title = Util.normalizeText(divTitle.h3.a.text)
            img = None
            if video.picture.img != None:
              img = video.picture.img['src']
            li = Util.createListItem(title, thumbnailImage = img, streamtype = 'video', infolabels = { 'title' : title }, isPlayable = True)
            xbmcplugin.addDirectoryItem(self._handle, Util.formatUrl({ 'id' : 'v', 'page' : divTitle.h3.a['href'] }), li, False)

          # Next page.
          nextPage = response.find('ul', 'swiper-wrapper jgrid')
          if nextPage != None:
            pages = nextPage.findAll('li')
            index = -1
            for page in pages:
              if page.a['class'] == 'active cc':
                index = pages.index(page) + 1
                break # Stops "for page in pages:".
            if index < len(pages):
              url = Util.formatUrl({ 'id' : 'c', 'page' : pages[index].a['href'] })
              xbmcplugin.addDirectoryItem(self._handle, url, Util.createItemPage(Util.normalizeText(pages[index].a.text)), True)

          # Show items.
          xbmcplugin.endOfDirectory(self._handle)

        # Play video.
        elif self._params['id'] == 'v':
          title = Util.normalizeText(response.find('meta', { 'name' : 'EdTitle' })['content'])
          img = response.find('meta', { 'name' : 'EdImage' })['content']
          descr = response.find('div', 'tv-desc-body').text

          # Video del fatto.
          videoId = response.find('param', { 'name' : '@videoPlayer' })
          if videoId != None:
            playerID = 2274739660001
            publisherID = 1328010481001
            const = 'ef59d16acbb13614346264dfe58844284718fb7b'
            conn = httplib.HTTPConnection('c.brightcove.com')
            envelope = remoting.Envelope(amfVersion=3)
            envelope.bodies.append(('/1', remoting.Request(target='com.brightcove.player.runtime.PlayerMediaFacade.findMediaById', body=[const, playerID, videoId['value'], publisherID], envelope=envelope)))
            conn.request('POST', '/services/messagebroker/amf?playerId={0}'.format(str(playerID)), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
            response = conn.getresponse().read()
            response = remoting.decode(response).bodies[0][1].body

            if response != None:
              item = sorted(response['renditions'], key=lambda item: item['encodingRate'], reverse=True)[0]
              streamUrl = item['defaultURL']

              # Divido url da playpath.
              index = streamUrl.find('&')
              url = streamUrl[:index]
              playpath = streamUrl[index + 1:]

              # Divido url da app.
              index = url.find('/', 7)
              app = url[index + 1:]
              if app[-1:] == '/':
                app = app[:-1]

              Util.playStream(self._handle, title, img, '{0}:1935 app={1} playpath={2}'.format(url[:index], app, playpath), 'video', { 'title' : title, 'plot' : descr })
            else:
              Util.showVideoNotAvailableDialog()

          # Altri video.
          else:
            responseString = response.renderContents()

            # Video di youtube.
            if responseString.find('www.youtube.com/embed') > -1:
              videoId = re.compile('http://www.youtube.com/embed/(.+?)\?').findall(response.find('iframe')['src'])
              if len(videoId) > 0:
                Util.playStream(self._handle, title, img, 'plugin://plugin.video.youtube/play/?video_id={0}'.format(videoId[0]), 'video', { 'title' : title, 'plot' : descr })

            # Video servizio pubblico.
            elif responseString.find('meride-video-container') > -1:
              params = { 'id' : 'e', 'page' : self._params['page'], 'title' : title, 'img' : img, 'descr' : descr }
              url = Util.formatUrl(params, 'plugin://plugin.video.serviziopubblico/')
              Util.playStream(self._handle, title, img, url, 'video', { 'title' : title, 'plot' : descr })

            # Video non gestito.
            else:
              Util.showVideoNotAvailableDialog()


# Entry point.
#startTime = datetime.datetime.now()
fc = FattoQTV()
del fc
#print '{0} azione {1}'.format(Util._addonName, str(datetime.datetime.now() - startTime))
